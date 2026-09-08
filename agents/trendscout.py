"""
agents/trendscout.py — Topic research (Section 6, agent #1).

Ab tak topics ek hardcoded SEED_TOPICS list se aate the. Ye agent unhe
ASLI DATA se nikalta hai.

Section 6 ke rules:
  * Apne pichhle videos ke performance patterns padho (playlistItems.list, 1 unit)
  * Niche ke andar topic clusters nikalo
  * ⚠️ KABHI BHI search.list mat use karo (100 units) jab tak bilkul zaroori na ho
  * Output: 5 topic candidates + predicted score

QUOTA MATH (yahi is agent ka poora design decide karta hai):
    search.list         = 100 units/call  →  poore din mein 100 calls ka budget khatam
    playlistItems.list  =   1 unit/call   →  100x sasta
    videos.list         =   1 unit/call
  Matlab: apne channel ka poora data ~2-3 units mein mil jaata hai.
  Ek search.list call utni hi mehngi hai jitni 100 din ka apna data.

TOPIC KAHAN SE AATE HAIN (teen source, kramvaar):
  1. WINNERS  — jo topics chal chuke hain, unke patterns (asli data)
  2. SERIES   — "Case #1, #2, #3..." binge behaviour banata hai (Section 8)
  3. LLM      — niche ke andar naye clusters (learnings ke saath)

⚠️ IMANDARI: "predicted score" ek HEURISTIC hai, koi ML model nahi. Wo apne
   pichhle data ke patterns pe based hai. Jab tak 10+ videos ka data na ho,
   ye lagbhag andaaza hai — aur code ye saaf batata hai.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from core.config import CONFIG
from core.db import DB
from core.llm import LLM
from core.logbook import Logbook
from core.quota import Quota, QuotaExceeded

log = Logbook("trendscout")

YT_API = "https://www.googleapis.com/youtube/v3"

# Series formats — Section 8: "binge behaviour banata hai"
SERIES_TEMPLATES = [
    "Case #{n}",
    "Unsolved #{n}",
    "File #{n}",
]

# Kitne topics suggest karne hain
N_CANDIDATES = 5


class TrendScout:
    def __init__(self, db: DB | None = None, llm: LLM | None = None,
                 quota: Quota | None = None, creds=None):
        self.db = db or DB()
        self.llm = (llm.for_agent("trendscout") if hasattr(llm, "for_agent") else llm) if llm else LLM(agent_name="trendscout")
        self.quota = quota or Quota(self.db)
        self._creds = creds

    # ==================================================================
    def scout(self, n: int = N_CANDIDATES) -> list[dict]:
        """
        Main entry point. Return: [{"topic", "score", "why", "source", "series"}, ...]
        Score ke hisaab se sorted.
        """
        patterns = self.own_patterns()
        candidates = []

        # ---- 1. LLM se naye topics (winners ke patterns ke saath) ----
        candidates.extend(self._llm_topics(patterns, n))

        # ---- 2. SERIES continuation ----
        # ⚠️ Series ka apna koi topic nahi hota — wo ek WRAPPER hai kisi topic ke
        # upar ("Case #5: <topic>"). Isliye pehle LLM topic lo, phir usse series
        # mein wrap karo. (Pehle ye alag candidate tha jiska topic=None hota tha,
        # aur caller ko dono cases handle karne padte the — bura design tha.)
        series = self._series_candidate(patterns)
        if series and candidates:
            best_llm = candidates[0]
            candidates.insert(0, {**best_llm, **series, "topic": best_llm["topic"]})

        # ---- 3. dedupe + score ----
        # Ab har candidate mein 'topic' HAMESHA hota hai — koi None nahi.
        seen, out = set(), []
        used = {self._norm(t) for t in self._recent_topics(40)}
        for c in candidates:
            key = self._norm(c.get("topic") or "")
            if not key or key in seen or key in used:
                continue
            seen.add(key)
            c["score"] = round(self._score(c, patterns), 3)
            out.append(c)

        out.sort(key=lambda c: -c["score"])
        out = out[:n]

        log.ok(f"{len(out)} topic candidates ready",
               best=(out[0].get("topic") or "")[:50] if out else None,
               data_points=patterns["n_videos"])
        self.db.log_event("scout", "trendscout", None,
                          candidates=[c["topic"] for c in out],
                          confidence=patterns["confidence"])
        return out

    def best_topic(self) -> str:
        """Ek topic do — run.py isse call karta hai."""
        c = self.scout(1)
        if c:
            return c[0]["topic"]
        return self._fallback_topic()

    # ==================================================================
    # APNE DATA KE PATTERNS
    # ==================================================================
    def own_patterns(self) -> dict:
        """
        Apne pichhle videos se kya seekha ja sakta hai.
        Ye SIRF apni DB se aata hai — koi API call nahi (0 units).
        """
        rows = self.db.q("""
            SELECT v.id, v.topic, v.title, v.hook_type, v.series_name, v.series_index,
                   m.views, m.avg_pct, m.comments, m.shares
            FROM videos v JOIN metrics m ON m.video_id = v.id
            WHERE m.window='2h' AND m.views IS NOT NULL
            ORDER BY m.views DESC LIMIT 40""")

        n = len(rows)
        if n == 0:
            return {"n_videos": 0, "confidence": "none", "winners": [],
                    "keywords": [], "avg_views": 0, "series": None}

        views = [r["views"] for r in rows]
        avg = sum(views) / len(views)
        winners = [dict(r) for r in rows[:max(1, n // 3)]]   # top third
        losers = [dict(r) for r in rows[-max(1, n // 3):]]

        # keyword extraction — winners ke titles/topics se
        win_kw = self._keywords([f"{r['topic']} {r['title'] or ''}" for r in winners])
        lose_kw = self._keywords([f"{r['topic']} {r['title'] or ''}" for r in losers])
        # jo winners mein hai par losers mein nahi — wahi asli signal hai
        signal = [k for k, c in win_kw.items() if c >= 2 and lose_kw.get(k, 0) < c]

        # confidence — kitna data hai uske hisaab se
        conf = "none" if n == 0 else "low" if n < 5 else "medium" if n < 15 else "high"

        # koi series chal rahi hai?
        srow = self.db.one("""SELECT series_name, MAX(series_index) mx, COUNT(*) n
                              FROM videos WHERE series_name IS NOT NULL
                              GROUP BY series_name ORDER BY n DESC LIMIT 1""")

        return {
            "n_videos": n, "confidence": conf, "avg_views": round(avg, 1),
            "winners": winners[:5], "keywords": signal[:12],
            "top_topics": [r["topic"] for r in winners[:5]],
            "weak_topics": [r["topic"] for r in losers[:3]],
            "series": ({"name": srow["series_name"], "next": (srow["mx"] or 0) + 1}
                       if srow else None),
        }

    @staticmethod
    def _keywords(texts: list[str]) -> dict:
        """Simple keyword frequency. Stopwords hataye hue (Hindi + English)."""
        stop = {
            "the", "a", "an", "is", "was", "were", "of", "in", "on", "at", "to",
            "and", "or", "but", "that", "this", "it", "its", "for", "with", "from",
            "ka", "ki", "ke", "ko", "se", "me", "mein", "hai", "tha", "thi", "the",
            "ek", "jo", "wo", "ye", "aur", "par", "bhi", "kya", "nahi", "hi", "kar",
            "raat", "case", "file",   # ye itne common hain ki signal nahi dete
        }
        freq: dict[str, int] = {}
        for t in texts:
            for w in re.findall(r"[\w\u0900-\u097F]+", (t or "").lower()):
                if len(w) < 3 or w in stop or w.isdigit():
                    continue
                freq[w] = freq.get(w, 0) + 1
        return dict(sorted(freq.items(), key=lambda kv: -kv[1]))

    # ==================================================================
    # YOUTUBE SE APNA DATA (sasta tareeka)
    # ==================================================================
    def sync_from_youtube(self, max_results: int = 25) -> dict:
        """
        Apne channel ke videos ka data kheencho — SASTE tareeke se.

        ⚠️ search.list (100 units) ki jagah:
             channels.list      (1 unit)  -> uploads playlist ID
             playlistItems.list (1 unit)  -> video IDs
             videos.list        (1 unit)  -> statistics
        Total: 3 units. search.list akela 100 units leta.
        """
        from core.oauth import api_request, authorize
        creds = self._creds or authorize()

        # ---- 1. uploads playlist ----
        self.quota.yt_call("channels.list", reason="trendscout: uploads playlist")
        st, data, _ = api_request(creds, f"{YT_API}/channels?part=contentDetails&mine=true")
        if st != 200 or not data.get("items"):
            raise RuntimeError(f"channels.list fail: {st} {json.dumps(data)[:200]}")
        uploads = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # ---- 2. video IDs (1 unit, chahe 50 videos hon) ----
        self.quota.yt_call("playlistItems.list", reason="trendscout: video list")
        st, data, _ = api_request(
            creds, f"{YT_API}/playlistItems?part=contentDetails"
                   f"&playlistId={uploads}&maxResults={min(50, max_results)}")
        if st != 200:
            raise RuntimeError(f"playlistItems fail: {st}")
        vids = [i["contentDetails"]["videoId"] for i in data.get("items", [])]
        if not vids:
            return {"synced": 0, "units_used": 2}

        # ---- 3. statistics (1 unit, 50 videos tak) ----
        self.quota.yt_call("videos.list", reason="trendscout: stats")
        st, data, _ = api_request(
            creds, f"{YT_API}/videos?part=snippet,statistics&id={','.join(vids[:50])}")
        if st != 200:
            raise RuntimeError(f"videos.list fail: {st}")

        synced = 0
        for item in data.get("items", []):
            row = self.db.one("SELECT id FROM videos WHERE yt_video_id=?", (item["id"],))
            if not row:
                continue     # ye video AUTOPILOT ne nahi banaya
            s = item.get("statistics", {})
            self.db.save_metrics(row["id"], "youtube", "7d",
                                 views=int(s.get("viewCount", 0) or 0),
                                 likes=int(s.get("likeCount", 0) or 0),
                                 comments=int(s.get("commentCount", 0) or 0),
                                 raw_json={"source": "trendscout_sync"})
            synced += 1

        log.ok(f"{synced} videos ka data sync hua — sirf 3 units kharch",
               note="search.list se ye 100 units leta")
        return {"synced": synced, "units_used": 3,
                "saved_vs_search": 100 - 3}

    # ==================================================================
    # TOPIC GENERATION
    # ==================================================================
    def _series_candidate(self, patterns: dict) -> dict | None:
        """
        Section 8: "Series formats — Case #1, #2, #3... binge behaviour banata hai"
        Agar koi series chal rahi hai to usse continue karo.
        """
        s = patterns.get("series")
        if not s:
            # koi series nahi — nayi shuru karo (par tabhi jab kuch videos ban chuke hon)
            if patterns["n_videos"] < 3:
                return None
            name = SERIES_TEMPLATES[0]
            return {"topic": None, "series": {"name": "Case", "index": 1},
                    "source": "series_new",
                    "why": "Nayi series shuru — binge behaviour banti hai"}
        return {"topic": None, "series": {"name": s["name"], "index": s["next"]},
                "source": "series",
                "why": f"{s['name']} #{s['next']} — series continue, binge behaviour"}

    def _llm_topics(self, patterns: dict, n: int) -> list[dict]:
        """LLM se topics — apne winners ke patterns aur learnings ke saath."""
        learnings = self.db.active_learnings()
        learn_txt = "\n".join(
            f"- {r['variable']}: '{r['winner']}' > '{r['loser']}' ({r['lift_pct']:+.0f}%)"
            for r in learnings[:6]) or "(abhi koi learning nahi)"

        if patterns["n_videos"] > 0:
            data_block = f"""
APNE DATA SE (n={patterns['n_videos']} videos, confidence={patterns['confidence']}):
  Ye topics ACCHE chale:
{chr(10).join('    - ' + t for t in patterns['top_topics'])}
  Ye KAMZOR rahe:
{chr(10).join('    - ' + t for t in patterns['weak_topics'])}
  Winners mein baar-baar aane wale shabd: {', '.join(patterns['keywords']) or '(abhi pattern nahi)'}
  Average 2h views: {patterns['avg_views']}
"""
        else:
            data_block = ("\nAPNE DATA SE: abhi koi data nahi hai (naya channel). "
                          "Isliye niche ke best practices follow karo.\n")

        prompt = f"""Tum ek content strategist ho jo viral short-form video topics dhoondhta hai.

NICHE: {CONFIG['niche']}
LANGUAGE: {CONFIG['language']}
AUDIENCE: {CONFIG['target_audience']}
{data_block}
JO PEHLE SEEKHA:
{learn_txt}

YE TOPICS HAAL HI MEIN USE HO CHUKE HAIN — inse ALAG jao:
{json.dumps(self._recent_topics(25), ensure_ascii=False)}

RULES:
1. Har topic ek THOS kahani ho — abstract theme nahi.
   ❌ "Purane ghar ke rahasya"   ✅ "Wo ghar jahan har naya kirayedar 3 din mein bhaag gaya"
2. Topic mein ek CONCRETE detail ho (number, jagah, waqt) — wo curiosity banati hai.
3. {CONFIG['video_length_sec']} second mein poori kahani aani chahiye — bahut badi mat lo.
4. Real ya folklore-based ho sakta hai, par KOI REAL ZINDA VYAKTI ka naam nahi
   (defamation risk) aur koi copyrighted story nahi.
5. Har topic alag TYPE ka ho — sab ek jaise nahi.

{n} topics do. Sirf JSON:
{{
  "topics": [
    {{"topic": "ek line ka thos topic {CONFIG['language']} mein",
      "why": "ye kyun chalega, ek line",
      "hook_angle": "sabse chaunkane wali detail kya hai"}}
  ]
}}"""

        data = self.llm.json(prompt)
        items = data.get("topics") or []
        if not isinstance(items, list):
            items = []

        out = []
        for it in items[:n + 2]:
            if not isinstance(it, dict):
                continue
            t = str(it.get("topic") or "").strip()
            if len(t) < 10:
                continue
            out.append({"topic": t[:200], "source": "llm",
                        "why": str(it.get("why") or "")[:160],
                        "hook_angle": str(it.get("hook_angle") or "")[:160],
                        "series": None})
        if not out:
            log.warn("LLM se koi topic nahi mila — fallback use kar rahe hain")
            out = [{"topic": self._fallback_topic(), "source": "fallback",
                    "why": "LLM fail hua", "series": None}]
        return out

    # ==================================================================
    def _score(self, cand: dict, patterns: dict) -> float:
        """
        Predicted score 0-1.

        ⚠️ Ye ek HEURISTIC hai, ML model nahi. Jab tak 10+ videos ka data na ho,
        ye lagbhag andaaza hai. Isliye confidence bhi report hoti hai.
        """
        score = 0.5     # neutral base

        # ---- series ko boost (binge behaviour, Section 8) ----
        if cand.get("series"):
            score += 0.15

        topic = (cand.get("topic") or "").lower()

        # ---- winner keywords ka overlap ----
        if patterns["keywords"] and topic:
            hits = sum(1 for k in patterns["keywords"] if k in topic)
            score += min(0.20, hits * 0.07)

        # ---- concrete detail (number/time) hai? ----
        if re.search(r"\d", topic):
            score += 0.10      # number = concreteness = curiosity

        # ---- lambai theek hai? ----
        words = len(topic.split())
        if 6 <= words <= 16:
            score += 0.05
        elif words > 22:
            score -= 0.10      # itna bada topic 32s mein nahi aayega

        # ---- data kam hai to score ko neutral ki taraf kheencho ----
        # (honest: bina data ke confident hona jhooth hai)
        damp = {"none": 0.25, "low": 0.5, "medium": 0.8, "high": 1.0}[patterns["confidence"]]
        score = 0.5 + (score - 0.5) * damp

        return max(0.0, min(1.0, score))

    # ==================================================================
    def _recent_topics(self, n: int) -> list[str]:
        return [r["topic"] for r in self.db.recent_videos(n) if r["topic"]]

    @staticmethod
    def _norm(t: str) -> str:
        return re.sub(r"[^\w\u0900-\u097F]+", " ", (t or "").lower()).strip()

    def _fallback_topic(self) -> str:
        """Sab fail ho jaye to bhi kuch to chahiye."""
        base = [
            "Ek gaon jahan se chaudah log ek hi raat mein gayab ho gaye",
            "Wo train jo 1911 mein nikli aur kabhi pahunchi hi nahi",
            "Ek chithi jo likhi jaane se pehle hi mil gayi thi",
            "Wo kamra jise chalis saal se kisi ne khola nahi",
            "Ek phone number jo har raat teen bajkar tetis minute pe call karta tha",
        ]
        used = {self._norm(t) for t in self._recent_topics(40)}
        for t in base:
            if self._norm(t) not in used:
                return t
        return base[0]

    # ==================================================================
    def report(self) -> str:
        p = self.own_patterns()
        L = ["🔍 TRENDSCOUT REPORT", "=" * 62]
        L.append(f"Apna data: {p['n_videos']} videos (confidence: {p['confidence']})")
        if p["n_videos"]:
            L.append(f"Average 2h views: {p['avg_views']}")
            L.append("\nJo chala:")
            for t in p["top_topics"]:
                L.append(f"  ✅ {t[:70]}")
            if p["weak_topics"]:
                L.append("Jo nahi chala:")
                for t in p["weak_topics"]:
                    L.append(f"  ❌ {t[:70]}")
            if p["keywords"]:
                L.append(f"\nWinners ke keywords: {', '.join(p['keywords'])}")
            else:
                L.append("\nAbhi koi keyword pattern nahi — aur data chahiye")
        else:
            L.append("Abhi koi published video nahi — topics niche best practices se aayenge")

        if p["series"]:
            L.append(f"\nSeries: {p['series']['name']} — agla #{p['series']['next']}")

        L.append("\nAgle topic candidates:")
        for c in self.scout():
            tag = f"[{c['source']}]"
            ser = c.get("series")
            name = (f"{ser['name']} #{ser['index']}: " if ser else "") + (c.get("topic") or "")
            L.append(f"  {c['score']:.2f} {tag:12} {name[:60]}")
            if c.get("why"):
                L.append(f"        └─ {c['why'][:70]}")

        L.append(f"\n⚠️ Score ek heuristic hai, ML model nahi. "
                 f"Confidence: {p['confidence']}.")
        L.append("💡 Quota: apna data 3 units mein aata hai "
                 "(search.list use karte to 100 lagte)")
        return "\n".join(L)


# =====================================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Topic research")
    ap.add_argument("--scout", action="store_true", help="topic candidates")
    ap.add_argument("--patterns", action="store_true", help="apne data ke patterns")
    ap.add_argument("--sync", action="store_true",
                    help="YouTube se apna data kheencho (3 units)")
    ap.add_argument("--best", action="store_true", help="sirf ek best topic")
    a = ap.parse_args()

    with DB() as db:
        ts = TrendScout(db)
        if a.scout:
            print(json.dumps(ts.scout(), indent=2, ensure_ascii=False))
        elif a.patterns:
            print(json.dumps(ts.own_patterns(), indent=2, ensure_ascii=False))
        elif a.sync:
            print(json.dumps(ts.sync_from_youtube(), indent=2, ensure_ascii=False))
        elif a.best:
            print(ts.best_topic())
        else:
            print(ts.report())
