"""
agents/analyst.py — Metrics fetch + retention analysis (Phase 7).

Section 6 ke rules:
  * Publish ke 2 GHANTE baad metrics kheencho — YE VELOCITY WINDOW HAI, sabse decisive
    (Section 3: "Velocity (pehle 2 ghante) = dominant. 2 ghante baad decision ho
     chuka hota hai. Iske baad growth sirf spillover hai.")
  * Phir 24h aur 7d pe
  * Retention curve nikalo, drop-off point identify karo
  * Compare karo: is video ka hook type / voice / template / publish time vs baseline
  * Output: "Ye video X% baseline se upar/neeche tha, kyunki ___"

QUOTA DISCIPLINE (Section 6):
  * `search.list` KABHI nahi (100 units). `playlistItems.list` (1 unit) ya
    `videos.list` (1 unit) use karo — 100x sasta.
  * YouTube Analytics API ka apna alag quota hai (Data API ke 10,000 units se alag)

THRESHOLDS (Section 3, research-backed):
  YouTube  : sub-30s videos ke liye ~65% retention, 30-60s ke liye ~50%
  Instagram: 3-second retention 60% se kam = distribution band
             overall 45-55% average (saves/shares bhi count hote hain)
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta, timezone

from core.db import DB
from core.logbook import Logbook
from core.oauth import Credentials, api_request
from core.quota import Quota, QuotaExceeded

log = Logbook("analyst")

YT_API = "https://www.googleapis.com/youtube/v3"
YT_ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"

# Section 3 ke thresholds. Inse neeche = distribution ruk jaati hai.
THRESHOLDS = {
    "yt_retention_short": 0.65,   # sub-30s videos
    "yt_retention_long": 0.50,    # 30-60s videos
    "ig_ret_3s": 0.60,            # IG ka sabse bada gate
    "ig_retention": 0.45,
}

# Kab metrics kheenchni hain (publish ke baad)
WINDOWS = {"2h": 2, "24h": 24, "7d": 168}


class Analyst:
    def __init__(self, db: DB | None = None, quota: Quota | None = None,
                 creds: Credentials | None = None):
        self.db = db or DB()
        self.quota = quota or Quota(self.db)
        self._creds = creds

    @property
    def creds(self) -> Credentials:
        if self._creds is None:
            from core.oauth import authorize
            self._creds = authorize()
        return self._creds

    # ==================================================================
    def due_videos(self) -> list[tuple[int, str]]:
        """
        Kaunse videos ki metrics abhi kheenchni hain?
        Return: [(video_id, window), ...]

        Logic: video publish hue X ghante ho gaye AND us window ki metrics
        abhi tak DB mein nahi hain.
        """
        now = datetime.now(timezone.utc)
        due = []
        for r in self.db.q("SELECT * FROM videos WHERE status='published' "
                           "AND published_ts IS NOT NULL ORDER BY id DESC LIMIT 100"):
            try:
                pub = datetime.fromisoformat(r["published_ts"])
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
            age_h = (now - pub).total_seconds() / 3600
            have = {m["window"] for m in self.db.get_metrics(r["id"])}
            for win, hours in WINDOWS.items():
                # window aa gaya hai, par thoda buffer bhi (2h window 2-6h ke beech)
                if age_h >= hours and win not in have:
                    due.append((r["id"], win))
        return due

    # ==================================================================
    def collect(self, video_id: int, window: str) -> dict:
        """Ek video ki metrics kheencho (dono platforms se) aur DB mein save karo."""
        row = self.db.get_video(video_id)
        if not row:
            raise ValueError(f"Video #{video_id} nahi mila")

        out = {}
        if row["yt_video_id"]:
            try:
                out["youtube"] = self._youtube(row, window)
            except QuotaExceeded as e:
                log.warn(f"YouTube metrics skip — quota: {e}")
            except Exception as e:  # noqa: BLE001
                log.error(f"YouTube metrics fail video #{video_id}", e)
        if row["ig_media_id"]:
            try:
                out["instagram"] = self._instagram(row, window)
            except Exception as e:  # noqa: BLE001
                log.error(f"IG metrics fail video #{video_id}", e)

        if not out:
            log.warn(f"Video #{video_id} ki koi metrics nahi mili "
                     f"(kahin publish hua hi nahi?)")
        return out

    # ------------------------------------------------------------------
    def _youtube(self, row, window: str) -> dict:
        """
        Do calls:
          1. videos.list (1 unit)          — views, likes, comments
          2. Analytics API (alag quota)    — retention curve, avg view %
        ⚠️ search.list KABHI nahi (100 units).
        """
        yt_id = row["yt_video_id"]
        self.quota.yt_call("videos.list", reason=f"metrics {window}")
        st, data, _ = api_request(
            self.creds, f"{YT_API}/videos?part=statistics,contentDetails&id={yt_id}")
        if st != 200 or not data.get("items"):
            raise RuntimeError(f"videos.list fail: {st} {json.dumps(data)[:200]}")

        stats = data["items"][0].get("statistics", {})
        m = {
            "views": int(stats.get("viewCount", 0) or 0),
            "likes": int(stats.get("likeCount", 0) or 0),
            "comments": int(stats.get("commentCount", 0) or 0),
            "raw_json": {"statistics": stats},
        }

        # ---- Analytics API: retention (alag quota, Data API units nahi lagte) ----
        try:
            m.update(self._yt_analytics(row, yt_id))
        except Exception as e:  # noqa: BLE001
            log.warn(f"YouTube Analytics skip: {str(e)[:150]}",
                     hint="'yt-analytics.readonly' scope chahiye — "
                          "token.json delete karke dobara authorize karo")

        self.db.save_metrics(row["id"], "youtube", window, **m)
        log.ok(f"YT metrics saved #{row['id']} @{window}",
               views=m["views"], ret_1s=m.get("ret_1s"), avg=m.get("avg_pct"))
        return m

    def _yt_analytics(self, row, yt_id: str) -> dict:
        """
        audienceRetention report — elapsedVideoTimeRatio vs audienceWatchRatio.
        Yahi se 1s aur 3s retention nikalti hai (Section 3 ke dominant signals).
        """
        pub = datetime.fromisoformat(row["published_ts"]).astimezone(timezone.utc)
        start = (pub - timedelta(days=1)).strftime("%Y-%m-%d")
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        url = (f"{YT_ANALYTICS}?ids=channel==MINE"
               f"&startDate={start}&endDate={end}"
               f"&metrics=audienceWatchRatio,relativeRetentionPerformance"
               f"&dimensions=elapsedVideoTimeRatio"
               f"&filters=video=={yt_id}")
        st, data, _ = api_request(self.creds, url)
        if st != 200:
            raise RuntimeError(f"Analytics {st}: {json.dumps(data)[:200]}")

        rows = data.get("rows") or []
        if not rows:
            return {}

        length = float(row["length_sec"] or 30)
        curve = [(float(r[0]), float(r[1])) for r in rows if len(r) >= 2]
        curve.sort()

        out = {
            "ret_1s": _ratio_at(curve, 1.0 / length),
            "ret_3s": _ratio_at(curve, 3.0 / length),
            "avg_pct": round(statistics.fmean(w for _, w in curve), 4) if curve else None,
            "raw_json": {"retention_curve": curve[:60]},
        }
        # ---- summary metrics (views se avg view duration) ----
        try:
            url2 = (f"{YT_ANALYTICS}?ids=channel==MINE&startDate={start}&endDate={end}"
                    f"&metrics=averageViewPercentage,shares,subscribersGained"
                    f"&filters=video=={yt_id}")
            st2, d2, _ = api_request(self.creds, url2)
            if st2 == 200 and d2.get("rows"):
                r = d2["rows"][0]
                out["avg_pct"] = round(float(r[0]) / 100, 4)
                out["shares"] = int(r[1] or 0)
        except Exception:  # noqa: BLE001
            pass
        return out

    # ------------------------------------------------------------------
    def _instagram(self, row, window: str) -> dict:
        """
        IG Insights. Reels ke liye available metrics:
          plays / reach / likes / comments / shares / saved / total_interactions
        ⚠️ IG per-second retention curve NAHI deta (YouTube deta hai).
           Ye ek asli limitation hai — hum ig_reels_avg_watch_time se estimate karte hain.
        """
        from agents.ig_publisher import InstagramPublisher
        ig = InstagramPublisher(self.db, self.quota)
        ig._require_creds()

        fields = ("plays,reach,likes,comments,shares,saved,total_interactions,"
                  "ig_reels_avg_watch_time,ig_reels_video_view_total_time")
        data = ig._call(f"/{row['ig_media_id']}/insights",
                        {"metric": fields, "access_token": ig.token},
                        what=f"insights {window}")

        vals = {}
        for item in data.get("data", []):
            v = (item.get("values") or [{}])[0].get("value", 0)
            vals[item.get("name")] = v

        plays = int(vals.get("plays", 0) or 0)
        length_ms = float(row["length_sec"] or 30) * 1000
        avg_watch_ms = float(vals.get("ig_reels_avg_watch_time", 0) or 0)

        m = {
            "views": plays,
            "likes": int(vals.get("likes", 0) or 0),
            "comments": int(vals.get("comments", 0) or 0),
            "shares": int(vals.get("shares", 0) or 0),
            "saves": int(vals.get("saved", 0) or 0),
            "avg_pct": round(avg_watch_ms / length_ms, 4) if length_ms else None,
            "raw_json": vals,
        }
        # replays estimate: total watch time / (plays * length)
        total_ms = float(vals.get("ig_reels_video_view_total_time", 0) or 0)
        if plays and length_ms:
            loops = total_ms / (plays * length_ms)
            m["replays"] = max(0, int((loops - 1) * plays))
        self.db.save_metrics(row["id"], "instagram", window, **m)
        log.ok(f"IG metrics saved #{row['id']} @{window}", plays=plays,
               avg=m["avg_pct"], saves=m["saves"])
        return m

    # ==================================================================
    def run(self, limit: int = 20) -> list[dict]:
        """Jitne videos due hain, sabki metrics kheencho. Cron isse call karega."""
        due = self.due_videos()[:limit]
        if not due:
            log.info("Abhi kisi video ki metrics due nahi hain")
            return []
        log.info(f"{len(due)} metric collections due hain")
        results = []
        for vid, win in due:
            try:
                data = self.collect(vid, win)
                if data:
                    results.append({"video_id": vid, "window": win, **data})
                    if win == "2h":
                        # velocity window — turant analyze karo, yahi decisive hai
                        self.analyze(vid, verdict_only=True)
            except Exception as e:  # noqa: BLE001
                log.error(f"Collection fail #{vid} @{win}", e)
        return results

    # ==================================================================
    # ANALYSIS — yahan se Scientist (Phase 8) ko input milta hai
    # ==================================================================
    def baseline(self, exclude_video: int | None = None, window: str = "2h",
                 min_n: int = 3) -> dict | None:
        """
        Baseline = pichhle videos ka average. Isse compare karke pata chalta hai
        ki ye video accha hai ya bura.
        """
        rows = self.db.q("""
            SELECT m.views, m.avg_pct, m.ret_1s, m.ret_3s, m.likes, m.comments,
                   m.shares, m.saves
            FROM metrics m JOIN videos v ON v.id = m.video_id
            WHERE m.window=? AND (? IS NULL OR m.video_id != ?)
            ORDER BY m.video_id DESC LIMIT 30""", (window, exclude_video, exclude_video))
        if len(rows) < min_n:
            return None
        def avg(key):
            vals = [r[key] for r in rows if r[key] is not None]
            return round(statistics.fmean(vals), 4) if vals else None
        return {"n": len(rows), "views": avg("views"), "avg_pct": avg("avg_pct"),
                "ret_1s": avg("ret_1s"), "ret_3s": avg("ret_3s"),
                "comments": avg("comments"), "shares": avg("shares")}

    # ------------------------------------------------------------------
    def analyze(self, video_id: int, window: str = "2h",
                verdict_only: bool = False) -> dict:
        """
        Ek video ka poora analysis:
          - baseline se kitna upar/neeche
          - retention threshold pass hua ya nahi
          - drop-off point kahan hai
          - KYUN (kaunsa variable) — ye Scientist ke liye input hai
        """
        row = self.db.get_video(video_id)
        mets = {m["window"]: dict(m) for m in self.db.get_metrics(video_id)}
        m = mets.get(window)
        if not m:
            return {"error": f"#{video_id} ki {window} metrics nahi hain"}

        base = self.baseline(exclude_video=video_id, window=window)
        length = float(row["length_sec"] or 30)
        reasons: list[str] = []
        flags: list[str] = []

        # ---- 1. VELOCITY (2h window) — sabse decisive ----
        vs_baseline = None
        if base and base["views"]:
            vs_baseline = round(100 * (m["views"] - base["views"]) / base["views"], 1)
            if vs_baseline >= 25:
                reasons.append(f"views baseline se {vs_baseline:+.0f}% upar "
                               f"(baseline {base['views']:.0f}, n={base['n']})")
            elif vs_baseline <= -25:
                reasons.append(f"views baseline se {vs_baseline:+.0f}% neeche")

        # ---- 2. RETENTION THRESHOLD (Section 3) ----
        plat = "youtube" if m["platform"] == "youtube" else "instagram"
        if plat == "youtube":
            need = (THRESHOLDS["yt_retention_short"] if length < 30
                    else THRESHOLDS["yt_retention_long"])
            got = m.get("avg_pct")
            if got is not None:
                if got < need:
                    flags.append("RETENTION_BELOW_THRESHOLD")
                    reasons.append(
                        f"retention {got*100:.0f}% hai, {length:.0f}s video ke liye "
                        f"{need*100:.0f}% chahiye — isse neeche distribution ruk jaati hai")
                else:
                    reasons.append(f"retention {got*100:.0f}% ✅ (threshold {need*100:.0f}%)")
            # 1-second retention = dominant signal
            r1 = m.get("ret_1s")
            if r1 is not None and r1 < 0.75:
                flags.append("WEAK_FIRST_SECOND")
                reasons.append(f"1-second retention sirf {r1*100:.0f}% — pehla frame "
                               f"aur pehli line kaam nahi kar rahe (ye YT ka sabse "
                               f"bada signal hai)")
        else:
            r3 = m.get("ret_3s") or m.get("avg_pct")
            if r3 is not None and r3 < THRESHOLDS["ig_ret_3s"]:
                flags.append("WEAK_3S")
                reasons.append(f"3-second retention {r3*100:.0f}% — IG ka gate "
                               f"{THRESHOLDS['ig_ret_3s']*100:.0f}% hai, isse neeche "
                               f"distribution band ho jaati hai")
            if m.get("saves"):
                reasons.append(f"{m['saves']} saves (IG mein saves ka weight bada hai)")

        # ---- 3. COMMENTS (5+ shabd wale hi ginte hain) ----
        if base and base.get("comments") is not None and m["comments"] is not None:
            if m["comments"] > (base["comments"] or 0) * 1.5 and m["comments"] >= 3:
                reasons.append(f"{m['comments']} comments — baseline se kaafi zyada, "
                               f"comment bait kaam kar raha hai")
            elif m["comments"] == 0 and m["views"] > 200:
                flags.append("NO_COMMENTS")
                reasons.append("zero comments — comment bait kaam nahi kar raha")

        # ---- 4. RE-WATCH / LOOP ----
        if m.get("replays") and m["views"]:
            rr = m["replays"] / m["views"]
            if rr > 0.15:
                reasons.append(f"replay rate {rr*100:.0f}% — loop ending kaam kar rahi hai")

        # ---- 5. DROP-OFF POINT ----
        drop = self.dropoff(video_id)
        if drop:
            reasons.append(f"sabse bada drop {drop['at_sec']:.1f}s pe "
                           f"({drop['drop_pct']:.0f}% viewers gaye)")
            if drop["at_sec"] < 3:
                flags.append("EARLY_DROPOFF")

        # ---- 6. VARIABLES (Scientist ke liye) ----
        variables = {"hook_type": row["hook_type"], "voice_id": row["voice_id"],
                     "template_id": row["template_id"],
                     "length_bucket": _bucket(length),
                     "publish_hour": (row["published_ts"] or "")[11:13]}

        verdict = _verdict(vs_baseline, flags)
        summary = (f"Video #{video_id} ({window}): {verdict}. "
                   + ("Kyunki " + "; ".join(reasons) + "." if reasons
                      else "Abhi comparison ke liye kaafi data nahi hai."))

        result = {
            "video_id": video_id, "window": window, "platform": m["platform"],
            "verdict": verdict, "vs_baseline_pct": vs_baseline,
            "flags": flags, "reasons": reasons, "variables": variables,
            "metrics": {k: m[k] for k in ("views", "likes", "comments", "shares",
                                          "saves", "avg_pct", "ret_1s", "ret_3s")},
            "baseline": base, "dropoff": drop, "summary": summary,
        }

        self.db.log_event("analysis", "analyst", video_id, **{
            "window": window, "verdict": verdict, "vs_baseline": vs_baseline,
            "flags": flags})
        if verdict_only:
            log.info(summary)
        return result

    # ------------------------------------------------------------------
    def dropoff(self, video_id: int) -> dict | None:
        """
        Retention curve se sabse bada drop dhoondho.
        Yahi wo jagah hai jahan script/visual fail ho raha hai.
        """
        rows = self.db.q("SELECT raw_json FROM metrics WHERE video_id=? "
                         "AND platform='youtube' AND raw_json IS NOT NULL "
                         "ORDER BY id DESC LIMIT 1", (video_id,))
        if not rows:
            return None
        try:
            curve = json.loads(rows[0]["raw_json"] or "{}").get("retention_curve")
        except json.JSONDecodeError:
            return None
        if not curve or len(curve) < 4:
            return None

        row = self.db.get_video(video_id)
        length = float(row["length_sec"] or 30)
        worst, worst_i = 0.0, 0
        for i in range(1, len(curve)):
            d = curve[i - 1][1] - curve[i][1]
            if d > worst:
                worst, worst_i = d, i
        if worst <= 0.02:
            return None
        return {"at_ratio": round(curve[worst_i][0], 3),
                "at_sec": round(curve[worst_i][0] * length, 1),
                "drop_pct": round(worst * 100, 1)}

    # ==================================================================
    def variable_report(self, window: str = "2h", min_n: int = 3) -> dict:
        """
        Har variable (hook_type, voice, template) ka average performance.
        Ye Scientist (Phase 8) ka raw material hai — par ye CORRELATION hai,
        causation nahi. Proper A/B Scientist karega.
        """
        out = {}
        for var in ("hook_type", "voice_id", "template_id"):
            rows = self.db.q(f"""
                SELECT v.{var} AS val, COUNT(*) n,
                       AVG(m.views) avg_views, AVG(m.avg_pct) avg_ret,
                       AVG(m.comments) avg_comments
                FROM videos v JOIN metrics m ON m.video_id = v.id
                WHERE m.window=? AND v.{var} IS NOT NULL
                GROUP BY v.{var} HAVING n >= ? ORDER BY avg_views DESC""",
                (window, min_n))
            if rows:
                out[var] = [{"value": r["val"], "n": r["n"],
                             "avg_views": round(r["avg_views"] or 0, 1),
                             "avg_retention": round(r["avg_ret"] or 0, 4),
                             "avg_comments": round(r["avg_comments"] or 0, 1)}
                            for r in rows]
        return out

    # ==================================================================
    def briefing(self) -> str:
        """Chief ke daily briefing ka analyst wala hissa — plain Hinglish."""
        lines = ["📊 ANALYST BRIEFING", "=" * 60]
        pub = self.db.q("SELECT COUNT(*) n FROM videos WHERE status='published'")[0]["n"]
        lines.append(f"Total published: {pub}")

        base = self.baseline(window="2h")
        if base:
            lines.append(f"Baseline (2h, n={base['n']}): {base['views']:.0f} views, "
                         f"retention {(base['avg_pct'] or 0)*100:.0f}%")
        else:
            lines.append("Baseline abhi nahi bana — kam se kam 3 videos ki metrics chahiye")

        recent = self.db.q("""SELECT v.id FROM videos v JOIN metrics m ON m.video_id=v.id
                              WHERE m.window='2h' ORDER BY v.id DESC LIMIT 5""")
        if recent:
            lines.append("\nPichhle videos:")
            for r in recent:
                a = self.analyze(r["id"], "2h")
                if "summary" in a:
                    lines.append(f"  • {a['summary'][:160]}")

        vr = self.variable_report()
        if vr:
            lines.append("\nVariable performance (correlation, causation nahi):")
            for var, items in vr.items():
                best = items[0]
                lines.append(f"  {var}: '{best['value']}' aage hai "
                             f"({best['avg_views']:.0f} views, n={best['n']})")
            lines.append("  ⚠️ Ye sirf correlation hai. Proper A/B ke liye Scientist "
                         "(Phase 8) chalega.")
        return "\n".join(lines)


# =====================================================================
def _ratio_at(curve: list[tuple[float, float]], ratio: float) -> float | None:
    """
    Retention curve pe kisi point ka watch ratio (linear interpolation).
    ratio=0 (video ka bilkul start) bhi valid hai — wahan retention ~1.0 hoti hai.
    """
    if not curve or ratio < 0:
        return None
    ratio = min(ratio, 1.0)
    prev = curve[0]
    for pt in curve:
        if pt[0] >= ratio:
            if pt[0] == prev[0]:
                return round(pt[1], 4)
            t = (ratio - prev[0]) / (pt[0] - prev[0])
            return round(prev[1] + t * (pt[1] - prev[1]), 4)
        prev = pt
    return round(curve[-1][1], 4)


def _bucket(length: float) -> str:
    if length < 22:
        return "<22s"
    if length < 30:
        return "22-30s"
    if length < 45:
        return "30-45s"
    return "45s+"


def _verdict(vs_baseline: float | None, flags: list[str]) -> str:
    if vs_baseline is None:
        return "baseline nahi hai (naya channel)"
    if "RETENTION_BELOW_THRESHOLD" in flags or "WEAK_3S" in flags:
        return f"KAMZOR ({vs_baseline:+.0f}% vs baseline) — retention threshold miss"
    if vs_baseline >= 50:
        return f"BAHUT ACCHA ({vs_baseline:+.0f}% vs baseline)"
    if vs_baseline >= 15:
        return f"ACCHA ({vs_baseline:+.0f}% vs baseline)"
    if vs_baseline <= -30:
        return f"KHARAB ({vs_baseline:+.0f}% vs baseline)"
    return f"AVERAGE ({vs_baseline:+.0f}% vs baseline)"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Metrics fetch + analysis")
    ap.add_argument("--run", action="store_true", help="jo due hai wo kheencho (cron)")
    ap.add_argument("--analyze", type=int, metavar="ID", help="ek video analyze karo")
    ap.add_argument("--window", default="2h", choices=["2h", "24h", "7d"])
    ap.add_argument("--briefing", action="store_true")
    ap.add_argument("--variables", action="store_true", help="variable report")
    ap.add_argument("--due", action="store_true", help="kya due hai wo dikhao")
    a = ap.parse_args()

    with DB() as db:
        an = Analyst(db)
        if a.analyze:
            print(json.dumps(an.analyze(a.analyze, a.window), indent=2, ensure_ascii=False))
        elif a.variables:
            print(json.dumps(an.variable_report(a.window), indent=2, ensure_ascii=False))
        elif a.due:
            d = an.due_videos()
            print(f"{len(d)} due:" if d else "Kuch due nahi hai")
            for vid, w in d:
                print(f"  #{vid} @{w}")
        elif a.run:
            print(json.dumps(an.run(), indent=2, ensure_ascii=False, default=str))
        else:
            print(an.briefing())
