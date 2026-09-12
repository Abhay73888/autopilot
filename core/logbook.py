"""
core/logbook.py — structured logging + audit trail.

Hard constraint #3: "Kabhi bhi silently fail mat karna."
Isliye har cheez do jagah jaati hai:
  1. Console pe — insaan ke padhne layak, Hinglish, rangeen
  2. logs/autopilot-YYYY-MM-DD.jsonl — machine ke padhne layak (dashboard isse padhega)

Extra: retry() helper — exponential backoff ke saath koi bhi function retry karta hai.
"""

from __future__ import annotations

import json
import random
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from .config import CONFIG

LEVELS = {"DEBUG": 10, "INFO": 20, "OK": 20, "WARN": 30, "ERROR": 40, "FATAL": 50}

# Terminal colours (Windows ke purane cmd pe ye ignore ho jayenge — koi dikkat nahi)
_COLOR = {
    "DEBUG": "\033[90m",
    "INFO": "\033[36m",
    "OK": "\033[32m",
    "WARN": "\033[33m",
    "ERROR": "\033[31m",
    "FATAL": "\033[1;41m",
}
_RESET = "\033[0m"

_EMOJI = {"DEBUG": "·", "INFO": "ℹ", "OK": "✅", "WARN": "⚠️", "ERROR": "❌", "FATAL": "💀"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Logbook:
    """Ek agent = ek Logbook instance. Naam se pata chalta hai kaun bol raha hai."""

    def __init__(self, agent: str = "system", min_level: str = "DEBUG"):
        self.agent = agent
        self.min_level = LEVELS.get(min_level.upper(), 10)
        self.log_dir = Path(CONFIG["log_dir"])
        self.log_dir.mkdir(parents=True, exist_ok=True)

    # ---------- internal ----------
    def _file(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"autopilot-{day}.jsonl"

    def _write(self, level: str, msg: str, **fields):
        if LEVELS.get(level, 0) < self.min_level:
            return
        record = {"ts": _now(), "level": level, "agent": self.agent, "msg": msg, **fields}
        # 1) JSONL file — kabhi crash nahi hona chahiye logging ki wajah se
        try:
            with self._file().open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except Exception:  # noqa: BLE001 — logging failure se program nahi rukna chahiye
            print("LOG WRITE FAILED:", traceback.format_exc(), file=sys.stderr)

        # 2) Console — insaan ke liye
        extra = " ".join(f"{k}={v}" for k, v in fields.items() if k != "trace")
        color = _COLOR.get(level, "")
        line = f"{color}{_EMOJI.get(level,'')} [{self.agent}] {msg}{_RESET}"
        if extra:
            line += f"  \033[90m({extra}){_RESET}"
        out_stream = sys.stderr if LEVELS.get(level, 0) >= 30 else sys.stdout
        try:
            print(line, file=out_stream)
        except UnicodeEncodeError:
            try:
                enc = getattr(out_stream, "encoding", "ascii") or "ascii"
                safe_line = line.encode(enc, errors="replace").decode(enc)
                print(safe_line, file=out_stream)
            except Exception:
                pass
        except OSError:
            # Windows background thread mein stdout/stderr invalid ho sakta hai
            # [Errno 22] Invalid argument — silently ignore, file log already hua
            pass
        except Exception:
            pass

    # ---------- public ----------
    def debug(self, msg, **f): self._write("DEBUG", msg, **f)
    def info(self, msg, **f): self._write("INFO", msg, **f)
    def ok(self, msg, **f): self._write("OK", msg, **f)
    def warn(self, msg, **f): self._write("WARN", msg, **f)
    def warning(self, msg, **f): self._write("WARN", msg, **f)


    def error(self, msg, exc: BaseException | None = None, **f):
        """Error log + Hinglish mein 'iska matlab kya hai' hint."""
        if exc is not None:
            f["error_type"] = type(exc).__name__
            f["error_detail"] = str(exc)[:400]
            f["trace"] = traceback.format_exc()[-2000:]
            f["hint"] = explain(exc)
        self._write("ERROR", msg, **f)
        if exc is not None:
            print(f"   \033[33m→ Matlab: {f['hint']}{_RESET}", file=sys.stderr)

    def fatal(self, msg, exc: BaseException | None = None, **f):
        self.error(msg, exc, **f)
        self._write("FATAL", "System ruk raha hai. Upar wali error dekho.")

    def audit(self, action: str, **f):
        """Audit trail — 'kis agent ne kya kiya' ka permanent record."""
        self._write("INFO", f"AUDIT: {action}", audit=True, action=action, **f)


# ---------------------------------------------------------------------
# Error ko plain Hinglish mein samjhane wali dictionary.
# Naya error mile to yahan ek line add kar dena — beginner ka time bachega.
# ---------------------------------------------------------------------
_EXPLAIN = [
    ("quotaExceeded", "YouTube ka daily quota khatam. Midnight Pacific Time pe reset hoga — kal try karo."),
    ("rateLimitExceeded", "Bahut tezi se calls gaye. Thoda ruk kar (backoff) retry hoga, ghabrao mat."),
    ("429", "Server keh raha hai 'dheere chalo'. Automatic backoff retry chalu hai."),
    ("403", "Permission ya quota ka issue. OAuth scope aur quota dashboard dono check karo."),
    ("401", "Token expire ho gaya ya galat hai. authorize_youtube.py dobara chalao."),
    ("invalid_grant", "Refresh token invalid ho gaya. token.json delete karke dobara authorize karo."),
    ("code\": 24", "Instagram format reject: video H.264 + AAC, MP4 container hona chahiye."),
    ("ModuleNotFoundError", "Koi Python package missing hai — `pip install -r requirements.txt` chalao."),
    ("FileNotFoundError", "File ya folder nahi mila. Path check karo (ya ffmpeg install nahi hai)."),
    ("ConnectionError", "Internet ya API tak pahunch nahi ho paayi. Net check karo, phir retry."),
    ("TimeoutError", "API ne time pe jawab nahi diya. Retry hoga; baar-baar ho to service down hogi."),
    ("database is locked", "SQLite pe do process ek saath likh rahe hain. Ek run band karo."),
    ("JSONDecodeError", "API ne JSON ki jagah kuch aur bheja (aksar HTML error page). Response log dekho."),
]


def explain(exc: BaseException | str) -> str:
    """Exception ya error-string ka Hinglish matlab lautao."""
    text = f"{type(exc).__name__}: {exc}" if isinstance(exc, BaseException) else str(exc)
    for needle, meaning in _EXPLAIN:
        if needle.lower() in text.lower():
            return meaning
    return "Ye naya error hai. Log file mein poora trace hai — usse padho ya SETUP.md ka troubleshooting dekho."


# ---------------------------------------------------------------------
# retry() — exponential backoff + jitter
# Acceptance test: "Har API failure retry hoti hai (exponential backoff) aur log hoti hai"
# ---------------------------------------------------------------------
def retry(fn, *, tries: int = 4, base_delay: float = 1.0, max_delay: float = 30.0,
          log: Logbook | None = None, what: str = "operation", sleep=time.sleep):
    """
    fn() ko chalao. Fail ho to 1s, 2s, 4s... ruk kar dobara try karo.
    `sleep` inject kar sakte ho taaki tests turant chalein.
    Saari koshishein fail ho jayein to aakhri exception raise hoti hai (silent fail nahi).
    """
    log = log or Logbook("retry")
    last = None
    for attempt in range(1, tries + 1):
        try:
            result = fn()
            if attempt > 1:
                log.ok(f"{what} attempt #{attempt} pe safal", attempts=attempt)
            return result
        except Exception as exc:  # noqa: BLE001 — yahan sab pakadna hi maqsad hai
            last = exc
            if attempt == tries:
                log.error(f"{what} {tries} koshishon ke baad bhi fail", exc)
                break
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay += random.uniform(0, delay * 0.25)  # jitter — sab retries ek saath na ho
            log.warn(f"{what} fail (koshish {attempt}/{tries}), {delay:.1f}s baad retry",
                     reason=str(exc)[:160], hint=explain(exc))
            sleep(delay)
    raise last  # type: ignore[misc]


log = Logbook("system")  # default shared logger

if __name__ == "__main__":
    lb = Logbook("demo")
    lb.info("Logbook test chal raha hai")
    lb.ok("Sab theek")
    lb.warn("Quota 80% cross")
    try:
        raise ValueError("403 quotaExceeded")
    except ValueError as e:
        lb.error("Demo error", e)
    print("Log file:", lb._file())
