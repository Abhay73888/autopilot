"""
core/quota.py — SABSE ZAROORI FILE. Ye poore system ko ban hone se bachati hai.

Rule (Section 9): HAR API call se PEHLE quota.can_spend() poochho.
Agar 'no' hai to call MAT karo — task queue mein daalo.

Do tarah ki windows hain:
  day_pacific  — YouTube ka quota Midnight Pacific Time pe reset hota hai
  rolling_24h  — Instagram ka publish limit rolling 24 ghante ka hai
  rolling_1h   — Instagram ka per-hour call limit

Extra: reconcile_from_headers() — Meta ke X-App-Usage headers padh kar
asli usage se apna hisaab milata hai (Section 2: "Inhe padho").
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo  # stdlib (Python 3.9+)

from .db import DB
from .logbook import Logbook

log = Logbook("quota")
PACIFIC = ZoneInfo("America/Los_Angeles")

# ---------------------------------------------------------------------
# BUDGETS — ye HAMARE safety caps hain, API ke asli limits se KAM.
# Kyun kam? Kyunki YouTube ka ek undocumented "~7 uploads/day" limit hai
# aur Instagram ke sources 50 vs 100 pe disagree karte hain.
# ---------------------------------------------------------------------
BUDGETS = {
    "youtube_units":   {"limit": 10000, "window": "day_pacific", "real": 10000,
                        "note": "YouTube Data API v3 daily units"},
    "youtube_uploads": {"limit": 5,     "window": "day_pacific", "real": 7,
                        "note": "Hidden limit ~7/day. Hum 5 pe rukte hain."},
    "youtube_search":  {"limit": 5,     "window": "day_pacific", "real": 100,
                        "note": "search.list = 100 units/call. Bachao! playlistItems (1 unit) use karo."},
    "ig_publishes":    {"limit": 20,    "window": "rolling_24h", "real": 50,
                        "note": "Docs 100 kehte hain, kuch sources 50. Hum 20."},
    "ig_calls_hour":   {"limit": 150,   "window": "rolling_1h",  "real": 200,
                        "note": "Container polling bhi isi mein ginti hai."},
    "gemini_requests": {"limit": 1200,  "window": "day_pacific", "real": 1500,
                        "note": "Gemini free tier RPD."},
}

# Har YouTube endpoint ki cost (units). Section 2 se.
YT_COST = {
    "videos.insert": 100,      # Dec 2025 se 1600 -> 100
    "videos.list": 1,
    "playlistItems.list": 1,   # channel ke videos lene ka SASTA tareeka
    "channels.list": 1,
    "search.list": 100,        # MEHNGA — bacho
    "commentThreads.insert": 50,
    "videos.update": 50,
    "playlists.list": 1,       # Phase 5: playlist dhoondhna
    "playlists.insert": 50,    # Phase 5: nayi playlist banana
    "playlistItems.insert": 50,  # Phase 5: video playlist mein daalna
}


class QuotaExceeded(Exception):
    """Budget khatam. Ye crash nahi hai — caller ko task queue karna chahiye."""


class Quota:
    def __init__(self, db: DB | None = None, budgets: dict | None = None):
        self.db = db or DB()
        self._own_db = db is None
        self.budgets = budgets or BUDGETS

    def close(self):
        if self._own_db:
            self.db.close()

    # ---------- window ka start time nikalo ----------
    def _window_start(self, window: str) -> datetime:
        now_utc = datetime.now(timezone.utc)
        if window == "day_pacific":
            # Pacific mein aaj ki aadhi raat -> UTC mein badlo
            pac_now = now_utc.astimezone(PACIFIC)
            pac_midnight = pac_now.replace(hour=0, minute=0, second=0, microsecond=0)
            return pac_midnight.astimezone(timezone.utc)
        if window == "rolling_24h":
            return now_utc - timedelta(hours=24)
        if window == "rolling_1h":
            return now_utc - timedelta(hours=1)
        raise ValueError(f"Unknown window: {window}")

    # ---------- kitna use ho chuka ----------
    def used(self, bucket: str) -> int:
        cfg = self._cfg(bucket)
        start = self._window_start(cfg["window"]).isoformat(timespec="seconds")
        row = self.db.one("SELECT COALESCE(SUM(amount),0) s FROM quota_usage WHERE bucket=? AND ts>=?",
                          (bucket, start))
        return int(row["s"] if row else 0)

    def remaining(self, bucket: str) -> int:
        return max(0, self._cfg(bucket)["limit"] - self.used(bucket))

    def _cfg(self, bucket: str) -> dict:
        if bucket not in self.budgets:
            raise KeyError(f"'{bucket}' budget defined nahi hai. quota.py ke BUDGETS mein add karo.")
        return self.budgets[bucket]

    # ---------- main API ----------
    def can_spend(self, bucket: str, amount: int = 1) -> bool:
        """Har API call se PEHLE ye poochho."""
        ok = self.remaining(bucket) >= amount
        if not ok:
            log.warn(f"BLOCKED: '{bucket}' ka budget khatam", used=self.used(bucket),
                     limit=self._cfg(bucket)["limit"], chahiye=amount,
                     reset=self.reset_in_human(bucket))
        return ok

    def spend(self, bucket: str, amount: int = 1, reason: str = "") -> None:
        """API call SAFAL hone ke baad ye call karo (ya check_and_spend use karo)."""
        self.db.conn.execute(
            "INSERT INTO quota_usage (ts,bucket,amount,reason) VALUES (?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), bucket, amount, reason))
        used, limit = self.used(bucket), self._cfg(bucket)["limit"]
        pct = 100 * used / limit if limit else 0
        if pct >= 80:  # Section 2: "80% cross ho to slow down"
            log.warn(f"'{bucket}' {pct:.0f}% use ho gaya — dheere chalo",
                     used=used, limit=limit, reset=self.reset_in_human(bucket))
        else:
            log.debug(f"spent {amount} {bucket}", used=used, limit=limit, reason=reason)

    def check_and_spend(self, bucket: str, amount: int = 1, reason: str = "") -> None:
        """Atomic: budget nahi hai to QuotaExceeded raise, warna kharch record."""
        if not self.can_spend(bucket, amount):
            raise QuotaExceeded(
                f"'{bucket}' budget khatam ({self.used(bucket)}/{self._cfg(bucket)['limit']}). "
                f"Reset: {self.reset_in_human(bucket)}. Task queue mein daal do.")
        self.spend(bucket, amount, reason)

    # YouTube ke liye shortcut — endpoint ka naam do, cost khud lag jayegi
    def yt_call(self, endpoint: str, reason: str = "") -> None:
        cost = YT_COST.get(endpoint)
        if cost is None:
            raise KeyError(f"'{endpoint}' ki cost pata nahi. YT_COST mein add karo.")
        if endpoint == "search.list":
            # Section 6: TrendScout ko search.list use hi nahi karna chahiye
            log.warn("search.list use ho raha hai (100 units!). "
                     "playlistItems.list se kaam ho sakta hai kya? Wo 1 unit hai.")
            self.check_and_spend("youtube_search", 1, reason or endpoint)
        self.check_and_spend("youtube_units", cost, reason or endpoint)
        if endpoint == "videos.insert":
            self.check_and_spend("youtube_uploads", 1, reason or "upload")

    # ---------- reset kab hoga ----------
    def reset_at(self, bucket: str) -> datetime:
        cfg = self._cfg(bucket)
        if cfg["window"] == "day_pacific":
            pac_now = datetime.now(timezone.utc).astimezone(PACIFIC)
            nxt = (pac_now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            return nxt.astimezone(timezone.utc)
        hours = 24 if cfg["window"] == "rolling_24h" else 1
        start = self._window_start(cfg["window"]).isoformat(timespec="seconds")
        row = self.db.one("SELECT MIN(ts) t FROM quota_usage WHERE bucket=? AND ts>=?", (bucket, start))
        oldest = row["t"] if row and row["t"] else None
        if not oldest:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(oldest) + timedelta(hours=hours)

    def reset_in_human(self, bucket: str) -> str:
        delta = self.reset_at(bucket) - datetime.now(timezone.utc)
        secs = max(0, int(delta.total_seconds()))
        h, m = secs // 3600, (secs % 3600) // 60
        return f"{h}h {m}m baad" if h else f"{m}m baad"

    # ---------- Meta headers se reconcile ----------
    def reconcile_from_headers(self, headers: dict) -> dict:
        """
        Instagram/Meta har response mein X-App-Usage bhejta hai:
            {"call_count":30,"total_cputime":10,"total_time":15}   # ye % hain
        Agar Meta ka % hamare hisaab se zyada hai to hum apna counter bada dete hain
        (matlab Meta ke hisaab pe bharosa karo, apne pe nahi).
        """
        out = {}
        for key in ("x-app-usage", "X-App-Usage", "x-business-use-case-usage",
                    "X-Business-Use-Case-Usage"):
            if key not in headers:
                continue
            try:
                data = json.loads(headers[key])
            except (json.JSONDecodeError, TypeError):
                log.warn("Usage header parse nahi hua", header=key, value=str(headers[key])[:120])
                continue
            pct = data.get("call_count", 0) if isinstance(data, dict) else 0
            out[key] = data
            if isinstance(pct, (int, float)) and pct:
                limit = self._cfg("ig_calls_hour")["limit"]
                meta_says = int(limit * pct / 100)
                gap = meta_says - self.used("ig_calls_hour")
                if gap > 0:
                    self.spend("ig_calls_hour", gap, reason=f"reconcile: Meta says {pct}%")
                if pct >= 80:
                    log.warn(f"Meta ka app-usage {pct}% — 1 ghanta slow down karo", header=key)
        return out

    # ---------- dashboard ----------
    def snapshot(self) -> dict:
        snap = {}
        for bucket, cfg in self.budgets.items():
            used = self.used(bucket)
            snap[bucket] = {
                "used": used, "limit": cfg["limit"],
                "remaining": max(0, cfg["limit"] - used),
                "pct": round(100 * used / cfg["limit"], 1) if cfg["limit"] else 0,
                "window": cfg["window"], "reset_in": self.reset_in_human(bucket),
                "note": cfg.get("note", ""),
            }
        return snap

    def print_report(self):
        print("\n📊 QUOTA REPORT")
        print("-" * 72)
        for b, s in self.snapshot().items():
            bar_len = int(s["pct"] / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            flag = "⚠️ " if s["pct"] >= 80 else "  "
            print(f"{flag}{b:18} {bar} {s['used']:>6}/{s['limit']:<6} reset {s['reset_in']}")
        print("-" * 72)


if __name__ == "__main__":
    q = Quota()
    q.print_report()
