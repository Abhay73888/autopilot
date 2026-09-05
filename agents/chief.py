"""
agents/chief.py — ORCHESTRATOR + SCHEDULER (Phase 9 + 10).

Section 6: "Sabko orchestrate karo, daily briefing do. Quota budget allocate karo.
Kya kaam kar raha hai / kya nahi — plain Hinglish mein batao."

Section 7 ka LEARNING LOOP yahan formally close hota hai:

    Publish
       ↓
    2h metrics ──→ velocity check ──→ agar dead hai, kyu?
       ↓
    24h + 7d metrics
       ↓
    Analyst: kaunsa variable correlate kar raha?
       ↓
    Scientist: agla experiment design karo
       ↓
    Learning DB mein save
       ↓
    Writer/ArtDirector/Voice agli baar ye learnings padhte hain   ← LOOP CLOSED
       ↓
    Loop

CHALANE KA TAREEKA:
    python -m agents.chief --tick        # ek cycle (cron har ghante isse chalayega)
    python -m agents.chief --digest      # subah ka digest
    python -m agents.chief --install-cron # cron setup ka guide

⚠️ SAFETY:
  * LOCK FILE — do process ek saath nahi chal sakte (warna double publish ho jayega)
  * Har task apne aap mein try/except — ek fail ho to baaki chalte rahein
  * autonomy=review_first mein publish NAHI hota, sirf queue banta hai
  * Quota khatam ho to kaam kal ke liye ruk jaata hai, crash nahi hota
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from core.quota import Quota

log = Logbook("chief")

ROOT = Path(CONFIG["_root"])
LOCK_FILE = ROOT / "data" / "chief.lock"
STATE_FILE = ROOT / "data" / "chief_state.json"
IST = ZoneInfo("Asia/Kolkata")

# Ek tick mein zyada se zyada kitna kaam
MAX_VIDEOS_PER_TICK = 1        # ek baar mein ek video — machine pe pressure kam
LOCK_STALE_MINUTES = 90        # itna purana lock = crashed process, hata do


# =====================================================================
# LOCK — double-run se bachav
# =====================================================================
class Lock:
    """
    Simple file lock. Do chief ek saath chale to double publish ho jayega
    (aur wo quota + reputation dono ka nuksaan hai).
    """

    def __init__(self, path: Path = LOCK_FILE):
        self.path = path
        self.acquired = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            age_min = (time.time() - self.path.stat().st_mtime) / 60
            try:
                info = json.loads(self.path.read_text())
            except Exception:  # noqa: BLE001
                info = {}
            if age_min < LOCK_STALE_MINUTES:
                raise RuntimeError(
                    f"Ek aur chief process pehle se chal raha hai "
                    f"(PID {info.get('pid')}, {age_min:.0f} min purana).\n"
                    f"→ Agar wo crash ho gaya tha to ye file delete kar do: {self.path}")
            log.warn(f"Purana lock mila ({age_min:.0f} min) — crashed process hoga, "
                     f"hata rahe hain")
            self.path.unlink(missing_ok=True)

        self.path.write_text(json.dumps({
            "pid": os.getpid(),
            "started": datetime.now(timezone.utc).isoformat(timespec="seconds")}))
        self.acquired = True
        return self

    def __exit__(self, *a):
        if self.acquired:
            self.path.unlink(missing_ok=True)


# =====================================================================
class Chief:
    def __init__(self, db: DB | None = None, dry_run: bool = False):
        self.db = db or DB()
        self.quota = Quota(self.db)
        self.dry_run = dry_run
        self.actions: list[str] = []
        self.errors: list[str] = []

    # ------------------------------------------------------------------
    def _do(self, name: str, fn, *args, **kw):
        """Ek task chalao. Fail ho to log karo par baaki tasks rukein nahi."""
        try:
            result = fn(*args, **kw)
            if result:
                self.actions.append(f"{name}: {result}")
            return result
        except Exception as e:  # noqa: BLE001
            msg = f"{name} fail: {type(e).__name__}: {str(e)[:180]}"
            self.errors.append(msg)
            log.error(f"Task '{name}' fail hua", e)
            self.db.log_event("task_failed", "chief", None, task=name, error=str(e)[:400])
            return None

    # ==================================================================
    # TICK — cron har ghante isse chalayega
    # ==================================================================
    def tick(self) -> dict:
        """
        Ek cycle. Har step apne aap decide karta hai ki abhi kuch karna hai ya nahi.
        Order maayne rakhta hai: pehle data collect, phir seekho, phir naya banao.
        """
        t0 = time.time()
        now_ist = datetime.now(IST)
        log.info(f"⏰ Chief tick — {now_ist:%d %b %H:%M} IST")
        self.actions, self.errors = [], []

        # ---- 1. METRICS (pehle — kyunki 2h velocity window miss nahi hona chahiye) ----
        self._do("metrics", self.task_metrics)

        # ---- 2. SCIENCE (metrics ke baad — naya data mila to evaluate karo) ----
        self._do("experiment", self.task_experiment)

        # ---- 3. PUBLISH (jo approved hai aur time ho gaya) ----
        self._do("publish", self.task_publish)

        # ---- 4. PRODUCE (aakhir mein — ye sabse slow hai) ----
        self._do("produce", self.task_produce)

        # ---- 5. HOUSEKEEPING ----
        self._do("cleanup", self.task_cleanup)

        elapsed = round(time.time() - t0, 1)
        state = self._load_state()
        state["last_tick"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        state["last_tick_actions"] = self.actions
        state["last_tick_errors"] = self.errors
        self._save_state(state)

        summary = {"ts": now_ist.isoformat(timespec="seconds"),
                   "elapsed_sec": elapsed, "actions": self.actions,
                   "errors": self.errors}
        self.db.log_event("tick", "chief", None, **summary)

        if self.actions:
            log.ok(f"Tick complete ({elapsed}s): " + " | ".join(self.actions))
        else:
            log.info(f"Tick complete ({elapsed}s) — abhi kuch karne ko nahi tha")
        if self.errors:
            log.warn(f"{len(self.errors)} task fail hue — digest mein detail hai")
        return summary

    # ==================================================================
    # TASK 1: metrics
    # ==================================================================
    def task_metrics(self) -> str | None:
        from agents.analyst import Analyst
        an = Analyst(self.db, self.quota)
        due = an.due_videos()
        if not due:
            return None
        if self.dry_run:
            return f"{len(due)} metrics due (dry-run, skip)"
        results = an.run(limit=10)
        return f"{len(results)} metrics collected" if results else None

    # ==================================================================
    # TASK 2: experiment lifecycle
    # ==================================================================
    def task_experiment(self) -> str | None:
        """
        Scientist ko aage badhao:
          - koi experiment chal raha hai aur ready hai -> conclude karo
          - koi nahi chal raha -> naya shuru karo
        """
        from agents.scientist import Scientist
        sci = Scientist(self.db)
        exp = self.db.running_experiment()

        if exp:
            ev = sci.evaluate()
            if ev.get("ready"):
                if self.dry_run:
                    return f"experiment #{exp['id']} conclude karne layak hai (dry-run)"
                res = sci.conclude()
                return res.get("verdict", "concluded")[:120]
            return None    # abhi data kam hai, chupchap intezaar karo

        # koi experiment nahi — naya shuru karo (par tabhi jab publish ho raha ho)
        published = self.db.q("SELECT COUNT(*) n FROM videos "
                              "WHERE status='published'")[0]["n"]
        if published < 4:
            return None    # itne kam videos pe experiment ka matlab nahi
        if self.dry_run:
            s = sci.suggest_next()
            return f"naya experiment suggest: {s['variable']}" if s else None
        r = sci.start()
        return (f"naya experiment #{r['experiment_id']}: {r['variable']} "
                f"({r['arm_a']} vs {r['arm_b']})") if r.get("ok") else None

    # ==================================================================
    # TASK 3: publish
    # ==================================================================
    def task_publish(self) -> str | None:
        """
        Approved videos ko publish karo — par sirf peak window mein.

        ⚠️ review_first mode mein sirf woh videos jaate hain jo insaan ne
        dashboard se approve kiye hain. auto_publish mein 'validated' bhi chalega.
        """
        autonomy = CONFIG.get("autonomy", "review_first")
        ready = self.db.videos_by_status("approved")

        if autonomy == "auto_publish":
            # review_first_count tak insaan ne dekha hai? tabhi auto
            done = self.db.q("SELECT COUNT(*) n FROM videos "
                             "WHERE status='published'")[0]["n"]
            need = int(CONFIG.get("review_first_count", 20))
            if done < need:
                log.info(f"auto_publish ON hai par abhi {done}/{need} videos hi "
                         f"publish hue — pehle {need} tak manual review behtar hai")
            else:
                ready = ready + self.db.videos_by_status("validated")

        if not ready:
            return None

        if not self._in_publish_window():
            return None

        # quota check
        if not self.quota.can_spend("youtube_uploads", 1):
            return (f"publish ruka — YT upload quota khatam "
                    f"({self.quota.reset_in_human('youtube_uploads')} reset)")

        row = ready[0]
        if self.dry_run:
            return f"video #{row['id']} publish hota (dry-run)"

        out = []
        # ---- YouTube ----
        try:
            from agents.publisher import YouTubePublisher
            r = YouTubePublisher(self.db, self.quota).publish(
                row["id"], privacy="private")   # ⚠️ hamesha private pehle
            out.append(f"YT {r.get('status')}")
        except Exception as e:  # noqa: BLE001
            self.errors.append(f"YT publish #{row['id']}: {str(e)[:150]}")

        # ---- Instagram ----
        if os.environ.get("IG_LONG_LIVED_TOKEN"):
            try:
                from agents.ig_publisher import InstagramPublisher
                r = InstagramPublisher(self.db, self.quota).publish(row["id"])
                out.append(f"IG {r.get('status')}")
            except Exception as e:  # noqa: BLE001
                self.errors.append(f"IG publish #{row['id']}: {str(e)[:150]}")

        return f"video #{row['id']} → " + ", ".join(out) if out else None

    def _in_publish_window(self) -> bool:
        """
        Section 8: "Velocity engineering — audience ke peak online window mein
        publish karo (apne hi analytics se seekho, guess mat karo)."
        """
        from agents.publisher import best_publish_time
        target = datetime.strptime(best_publish_time(self.db), "%Y-%m-%dT%H:%M:%SZ") \
            .replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        # target kal ka ho sakta hai — aaj ke usi ghante se compare karo
        today_target = now.replace(hour=target.hour, minute=target.minute,
                                   second=0, microsecond=0)
        diff_min = abs((now - today_target).total_seconds()) / 60
        inside = diff_min <= 45     # ±45 minute window
        if not inside:
            log.debug(f"Publish window nahi hai (peak {today_target:%H:%M} UTC, "
                      f"abhi {now:%H:%M})")
        return inside

    # ==================================================================
    # TASK 4: produce
    # ==================================================================
    def task_produce(self) -> str | None:
        """
        Naya video banao — par tabhi jab:
          - aaj ka target poora nahi hua
          - approve queue mein bahut backlog nahi hai
        """
        target = int(CONFIG.get("videos_per_day", 2))
        made_today = self._made_today()
        if made_today >= target:
            return None

        # backlog check — 5 se zyada pending hain to aur mat banao
        pending = len(self.db.videos_by_status("validated")) + \
            len(self.db.videos_by_status("approved"))
        if pending >= 5:
            log.info(f"{pending} videos approve queue mein pade hain — "
                     f"naya nahi bana rahe. Dashboard pe review karo.")
            return None

        if self.dry_run:
            return f"video banta ({made_today}/{target} aaj)"

        from run import one_video
        info = one_video(None, dry_run=False, with_images=True,
                         preset="veryfast", keep_temp=False)
        if not info:
            return None

        # ⭐ LOOP CLOSURE: naya video experiment mein daalo
        vid = self.db.q("SELECT id FROM videos ORDER BY id DESC LIMIT 1")[0]["id"]
        try:
            from agents.scientist import Scientist
            Scientist(self.db).assign(vid)
        except Exception as e:  # noqa: BLE001
            log.debug(f"Experiment assign skip: {str(e)[:80]}")

        return f"video #{vid} bana ({made_today + 1}/{target} aaj)"

    def _made_today(self) -> int:
        start = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.q("SELECT COUNT(*) n FROM videos WHERE created_ts >= ?",
                         (start.astimezone(timezone.utc).isoformat(timespec="seconds"),)
                         )[0]["n"]

    # ==================================================================
    # TASK 5: cleanup
    # ==================================================================
    def task_cleanup(self) -> str | None:
        """Purani learnings downgrade + rejected videos ki files delete."""
        self.db.expire_old_learnings()

        freed = 0
        for r in self.db.q("SELECT id, video_path FROM videos "
                           "WHERE status='rejected' AND video_path IS NOT NULL"):
            d = ROOT / "output" / f"video_{r['id']:04d}"
            if d.exists():
                size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
                if not self.dry_run:
                    import shutil
                    shutil.rmtree(d, ignore_errors=True)
                    self.db.update_video(r["id"], video_path=None)
                freed += size
        if freed > 1024 * 1024:
            return f"{freed // 1024 // 1024} MB free kiya (rejected videos)"
        return None

    # ==================================================================
    # DIGEST — subah ka email/print
    # ==================================================================
    def digest(self) -> str:
        """Plain Hinglish daily briefing. Section 6: 'kya kaam kar raha hai / kya nahi'."""
        from agents.analyst import Analyst
        from agents.scientist import Scientist

        now = datetime.now(IST)
        brand = str(CONFIG.get("brand_name", "AUTOPILOT"))[:20]
        title = f"🎬 {brand} — DAILY DIGEST — {now:%d %b %Y, %H:%M} IST"
        L = [f"╔{'═' * 64}╗", f"║ {title:<62} ║", f"╚{'═' * 64}╝", ""]

        # ---- MODE ----
        mode = CONFIG.get("autonomy", "review_first")
        L.append(f"Mode: {mode}" + ("  (tum approve karoge, tabhi publish hoga)"
                                     if mode == "review_first" else "  (auto publish ON)"))
        if CONFIG.get("mock_mode"):
            L.append("⚠️  MOCK MODE ON — content asli nahi hai. "
                     "config.yaml mein mock_mode: false karo.")
        L.append("")

        # ---- 1. AAJ KA KAAM ----
        L.append("─── 📦 PRODUCTION ───")
        counts = {r["status"]: r["n"] for r in self.db.q(
            "SELECT status, COUNT(*) n FROM videos GROUP BY status")}
        target = int(CONFIG.get("videos_per_day", 2))
        L.append(f"  Aaj bane      : {self._made_today()}/{target}")
        L.append(f"  Approve queue : {counts.get('validated', 0) + counts.get('rendered', 0)}"
                 f"  ← dashboard pe review karo")
        L.append(f"  Publish ready : {counts.get('approved', 0)}")
        L.append(f"  Published     : {counts.get('published', 0)} total")
        if counts.get("failed"):
            L.append(f"  ❌ Failed     : {counts['failed']}  ← logs dekho")
        L.append("")

        # ---- 2. PERFORMANCE ----
        L.append("─── 📊 PERFORMANCE ───")
        an = Analyst(self.db, self.quota)
        base = an.baseline(window="2h")
        if base:
            L.append(f"  Baseline (2h, n={base['n']}): {base['views']:.0f} views, "
                     f"retention {(base['avg_pct'] or 0) * 100:.0f}%")
            recent = self.db.q("""SELECT v.id FROM videos v JOIN metrics m ON m.video_id=v.id
                                  WHERE m.window='2h' ORDER BY v.id DESC LIMIT 3""")
            for r in recent:
                a = an.analyze(r["id"], "2h")
                if a.get("summary"):
                    L.append(f"  • {a['summary'][:150]}")
        else:
            L.append("  Baseline abhi nahi bana (3+ videos ki metrics chahiye)")
        due = len(an.due_videos())
        if due:
            L.append(f"  {due} videos ki metrics due hain")
        L.append("")

        # ---- 2b. NEXT TOPICS ----
        try:
            from agents.trendscout import TrendScout
            cands = TrendScout(self.db).scout(3)
            if cands:
                L.append("  Agle topics (TrendScout):")
                for c in cands[:3]:
                    name = c.get("topic") or f"{c['series']['name']} #{c['series']['index']}"
                    L.append(f"    {c['score']:.2f}  {name[:58]}")
        except Exception as e:  # noqa: BLE001
            log.debug(f"TrendScout digest skip: {str(e)[:80]}")
        L.append("")

        # ---- 3. SCIENCE ----
        L.append("─── 🧪 SCIENCE ───")
        sci = Scientist(self.db)
        exp = self.db.running_experiment()
        if exp:
            ev = sci.evaluate()
            L.append(f"  Experiment #{exp['id']}: {exp['variable']} — "
                     f"{exp['arm_a']} vs {exp['arm_b']}")
            if ev.get("ready"):
                L.append(f"  ➜ {ev['explanation'][:150]}")
                L.append(f"  ➜ {ev['recommendation'][:130]}")
            else:
                L.append(f"  ➜ {ev.get('status', '')}")
        else:
            s = sci.suggest_next()
            L.append(f"  Koi experiment nahi chal raha."
                     + (f" Agla: {s['variable']}" if s else ""))
        champs = sci.champions()
        if champs:
            L.append("  Champions (default ban chuke hain):")
            for var, c in champs.items():
                L.append(f"    {var:14} = {c['value']:18} {c['lift_pct']:+.0f}% "
                         f"(n={c['n']}, {c['confidence']})")
        else:
            L.append("  Abhi koi champion nahi — koi experiment poora nahi hua")
        L.append("")

        # ---- 4. QUOTA ----
        L.append("─── 📉 QUOTA ───")
        for b, s in self.quota.snapshot().items():
            bar = "█" * int(s["pct"] / 10) + "░" * (10 - int(s["pct"] / 10))
            flag = " ⚠️" if s["pct"] >= 80 else ""
            L.append(f"  {b:17} {bar} {s['used']:>5}/{s['limit']:<6} "
                     f"reset {s['reset_in']}{flag}")
        L.append("")

        # ---- 5. PROBLEMS ----
        state = self._load_state()
        errs = state.get("last_tick_errors") or []
        log_errors = self._recent_log_errors()
        if errs or log_errors:
            L.append("─── ⚠️  DHYAN DO ───")
            for e in errs[:5]:
                L.append(f"  • {e[:140]}")
            for e in log_errors[:5]:
                L.append(f"  • [{e['agent']}] {e['msg'][:120]}")
            L.append("")

        # ---- 6. TUMHE KYA KARNA HAI ----
        L.append("─── ✅ TUMHE KYA KARNA HAI ───")
        todos = self._todos(counts, base, exp, champs)
        if todos:
            for t in todos:
                L.append(f"  □ {t}")
        else:
            L.append("  Kuch nahi! Sab apne aap chal raha hai. ☕")
        L.append("")
        L.append(f"  Dashboard: python -m web.server")
        L.append("─" * 66)
        return "\n".join(L)

    def _todos(self, counts, base, exp, champs) -> list[str]:
        t = []
        q = counts.get("validated", 0) + counts.get("rendered", 0)
        if q:
            t.append(f"{q} videos approve queue mein hain — dashboard pe review karo")
        if counts.get("failed"):
            t.append(f"{counts['failed']} videos fail hue — `python -m pipeline.validate --all`")
        if CONFIG.get("mock_mode"):
            t.append("Gemini API key daalo aur mock_mode: false karo — "
                     "abhi content asli nahi hai")
        if not Path(ROOT / "token.json").exists():
            t.append("YouTube authorize karo: `python authorize_youtube.py`")
        if not os.environ.get("IG_LONG_LIVED_TOKEN"):
            t.append("Instagram token setup karo (SETUP.md STEP 6c)")
        if not base:
            t.append("Kuch videos publish karo — Analyst ko data chahiye")
        for b, s in self.quota.snapshot().items():
            if s["pct"] >= 90:
                t.append(f"Quota '{b}' {s['pct']:.0f}% — aaj aur kaam nahi hoga")
        pub = counts.get("published", 0)
        need = int(CONFIG.get("review_first_count", 20))
        if CONFIG.get("autonomy") == "review_first" and pub >= need:
            t.append(f"{pub} videos publish ho chuke — ab `autonomy: auto_publish` "
                     f"kar sakte ho (config.yaml)")
        return t

    def _recent_log_errors(self) -> list[dict]:
        lf = Path(CONFIG["log_dir"]) / f"autopilot-{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
        if not lf.exists():
            return []
        out = []
        for line in lf.read_text(encoding="utf-8").splitlines()[-300:]:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("level") in ("ERROR", "FATAL"):
                out.append(r)
        return out[-5:]

    # ==================================================================
    def _load_state(self) -> dict:
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}

    def _save_state(self, state: dict):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


# =====================================================================
CRON_GUIDE = r"""
╔══════════════════════════════════════════════════════════════════╗
║  ⏰ AUTOPILOT KO ROZ APNE AAP CHALANE KA SETUP                    ║
╚══════════════════════════════════════════════════════════════════╝

Chief har ghante ek "tick" chalata hai. Har tick khud decide karta hai ki
abhi kya karna hai (metrics, publish, naya video, ya kuch nahi).

────────────────────────────────────────────────────────────────────
 LINUX / MAC — cron
────────────────────────────────────────────────────────────────────

1. Terminal mein likho:
       crontab -e

2. Ye 2 lines add karo (PATH apne hisaab se badlo):

   # har ghante ek tick
   0 * * * * cd {root} && {python} -m agents.chief --tick >> {root}/logs/cron.log 2>&1

   # roz subah 8 baje digest
   0 8 * * * cd {root} && {python} -m agents.chief --digest >> {root}/logs/digest.log 2>&1

3. Save karo (nano mein Ctrl+O, Enter, Ctrl+X)

4. Check karo ki lag gaya:
       crontab -l

⚠️ Mac pe: System Settings → Privacy & Security → Full Disk Access mein
   `cron` ko permission deni pad sakti hai.

────────────────────────────────────────────────────────────────────
 WINDOWS — Task Scheduler
────────────────────────────────────────────────────────────────────

1. Start menu → "Task Scheduler" → Create Basic Task
2. Name: AUTOPILOT tick
3. Trigger: Daily → Repeat task every 1 hour, for a duration of 1 day
4. Action: Start a program
       Program : {python}
       Arguments: -m agents.chief --tick
       Start in : {root}
5. Finish. Phir digest ke liye ek aur task (daily 8 AM, --digest)

────────────────────────────────────────────────────────────────────
 TEST KARO (cron lagane se pehle)
────────────────────────────────────────────────────────────────────

    {python} -m agents.chief --tick --dry-run    # kuch badlega nahi
    {python} -m agents.chief --tick              # asli tick
    {python} -m agents.chief --digest            # digest dekho

────────────────────────────────────────────────────────────────────
 ⚠️ INSTAGRAM WALI ZAROORI BAAT
────────────────────────────────────────────────────────────────────

IG ka container 24 ghante mein expire hota hai, isliye pehle se schedule
nahi kar sakte. Matlab **cron chalu rehna ZAROORI hai** — machine band hogi
to IG post nahi jayega.

YouTube mein ye problem nahi (`publishAt` server-side hai — ek baar upload
ho gaya to YouTube khud time pe public kar dega).

Laptop roz band karte ho? To ek chhota free VPS (Oracle Cloud free tier)
ya Raspberry Pi behtar rahega.
"""


def cron_guide() -> str:
    return CRON_GUIDE.format(root=str(ROOT), python=sys.executable)


# =====================================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="AUTOPILOT orchestrator")
    ap.add_argument("--tick", action="store_true", help="ek cycle chalao")
    ap.add_argument("--digest", action="store_true", help="daily briefing")
    ap.add_argument("--dry-run", action="store_true", help="kuch badlo mat")
    ap.add_argument("--install-cron", action="store_true", help="cron setup guide")
    ap.add_argument("--loop", type=int, metavar="MIN",
                    help="har MIN minute pe tick (cron ke bina test ke liye)")
    a = ap.parse_args()

    if a.install_cron:
        print(cron_guide())
        sys.exit(0)

    if a.digest:
        with DB() as db:
            print(Chief(db).digest())
        sys.exit(0)

    if a.loop:
        print(f"Loop mode — har {a.loop} min pe tick. Ctrl+C se band karo.\n")
        try:
            while True:
                try:
                    with Lock(), DB() as db:
                        Chief(db, dry_run=a.dry_run).tick()
                except RuntimeError as e:
                    log.warn(str(e))
                time.sleep(a.loop * 60)
        except KeyboardInterrupt:
            print("\nBye!")
        sys.exit(0)

    if a.tick:
        try:
            with Lock(), DB() as db:
                out = Chief(db, dry_run=a.dry_run).tick()
            print(json.dumps(out, indent=2, ensure_ascii=False))
        except RuntimeError as e:
            log.warn(str(e))
            sys.exit(1)
        sys.exit(0)

    with DB() as db:
        print(Chief(db).digest())
