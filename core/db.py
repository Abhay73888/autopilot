r"""
core/db.py — SQLite database (stdlib, koi install nahi).

Tables:
  videos       — har banaya gaya video, uski state machine, aur uske "variables"
                 (hook_type, voice, template) taaki Analyst inhe compare kar sake
  metrics      — 2h / 24h / 7d snapshots (per platform)
  experiments  — A/B experiments (Scientist)
  learnings    — jo seekha (Section 7 ka schema)
  quota_usage  — har API call ka hisaab (quota.py isse use karta hai)
  events       — audit trail / approvals

State machine (videos.status):
  planned -> scripted -> rendered -> validated -> approved -> publishing -> published
                                              \-> rejected      \-> failed
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import CONFIG
from .logbook import Logbook

log = Logbook("db")

VALID_STATUS = [
    "planned", "scripted", "rendered", "validated", "approved",
    "rejected", "publishing", "published", "failed",
]

SCHEMA = """
PRAGMA journal_mode=WAL;          -- do process ek saath padh sakein
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS videos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_ts    TEXT NOT NULL,
    updated_ts    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'planned',
    topic         TEXT,
    title         TEXT,
    caption       TEXT,
    hashtags      TEXT,              -- JSON list
    script_json   TEXT,              -- word-level timing wala script
    -- ==== A/B ke variables: ek video = in variables ka ek combination ====
    hook_type     TEXT,              -- specific_outcome | pov | contrarian | question
    voice_id      TEXT,              -- rotation ke liye
    template_id   TEXT,              -- visual template rotation
    length_sec    REAL,
    series_name   TEXT,
    series_index  INTEGER,
    scene_pacing  TEXT DEFAULT 'standard', -- standard | dynamic_fast (retention-adaptive)
    experiment_id INTEGER,           -- kis experiment ka hissa hai
    variant       TEXT,              -- 'A' | 'B'
    -- ==== files ====
    video_path    TEXT,
    cover_path    TEXT,
    public_url    TEXT,              -- IG ko public URL chahiye
    -- ==== publish ====
    yt_video_id   TEXT,
    ig_media_id   TEXT,
    scheduled_ts  TEXT,
    published_ts  TEXT,
    ai_disclosed  INTEGER DEFAULT 1, -- hard constraint #4: hamesha 1
    notes         TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_sched  ON videos(scheduled_ts);

CREATE TABLE IF NOT EXISTS metrics (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id     INTEGER NOT NULL,
    platform     TEXT NOT NULL,      -- 'youtube' | 'instagram'
    window       TEXT NOT NULL,      -- '2h' | '24h' | '7d'
    ts           TEXT NOT NULL,
    views        INTEGER DEFAULT 0,
    likes        INTEGER DEFAULT 0,
    comments     INTEGER DEFAULT 0,
    shares       INTEGER DEFAULT 0,
    saves        INTEGER DEFAULT 0,
    avg_pct      REAL,               -- average view percentage (retention)
    ret_1s       REAL,               -- 1-second retention (YT ka dominant signal)
    ret_3s       REAL,               -- 3-second retention (IG ka gate)
    replays      INTEGER DEFAULT 0,
    raw_json     TEXT,
    UNIQUE(video_id, platform, window),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS experiments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_ts   TEXT NOT NULL,
    variable     TEXT NOT NULL,      -- ek time pe SIRF ek variable
    hypothesis   TEXT,
    arm_a        TEXT,
    arm_b        TEXT,
    min_per_arm  INTEGER DEFAULT 5,  -- Section 6: min 5 videos per arm
    status       TEXT DEFAULT 'running',   -- running | concluded | abandoned
    result_json  TEXT,
    concluded_ts TEXT
);

CREATE TABLE IF NOT EXISTS learnings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    variable     TEXT NOT NULL,
    winner       TEXT,
    loser        TEXT,
    lift_pct     REAL,
    sample_size  INTEGER,
    confidence   TEXT,               -- low | medium | high
    still_valid  INTEGER DEFAULT 1,
    source_exp   INTEGER,
    note         TEXT
);

CREATE TABLE IF NOT EXISTS quota_usage (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,         -- UTC ISO
    bucket    TEXT NOT NULL,         -- 'youtube_units' | 'ig_publishes' ...
    amount    INTEGER NOT NULL,
    reason    TEXT
);
CREATE INDEX IF NOT EXISTS idx_quota ON quota_usage(bucket, ts);

CREATE TABLE IF NOT EXISTS events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    agent     TEXT,
    kind      TEXT,                  -- 'approval' | 'error' | 'publish' | 'run'
    video_id  INTEGER,
    payload   TEXT
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DB:
    """Patla sa SQLite wrapper. `with DB() as db:` ya seedha DB() dono chalega."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or CONFIG["db_path"])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), timeout=15, isolation_level=None)
        self.conn.row_factory = sqlite3.Row  # rows ko dict jaisa padh sako
        self.conn.executescript(SCHEMA)
        try:
            self.conn.execute("ALTER TABLE videos ADD COLUMN scene_pacing TEXT DEFAULT 'standard'")
        except sqlite3.OperationalError:
            pass  # column already exists

    # ---------- plumbing ----------
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def close(self): self.conn.close()

    @contextmanager
    def tx(self):
        """Transaction: andar exception aaya to poora rollback."""
        cur = self.conn.cursor()
        cur.execute("BEGIN")
        try:
            yield cur
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise

    def q(self, sql: str, params=()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def one(self, sql: str, params=()) -> sqlite3.Row | None:
        return self.conn.execute(sql, params).fetchone()

    # ---------- videos ----------
    def create_video(self, topic: str, **fields) -> int:
        fields = {k: v for k, v in fields.items() if v is not None}
        if isinstance(fields.get("hashtags"), (list, tuple)):
            fields["hashtags"] = json.dumps(list(fields["hashtags"]), ensure_ascii=False)
        if isinstance(fields.get("script_json"), (dict, list)):
            fields["script_json"] = json.dumps(fields["script_json"], ensure_ascii=False)
        cols = ["created_ts", "updated_ts", "status", "topic", *fields.keys()]
        vals = [now(), now(), fields.pop("status", "planned") if "status" in fields else "planned", topic]
        # note: status ko dono jagah na jaane dein
        cols = ["created_ts", "updated_ts", "status", "topic", *fields.keys()]
        vals = [now(), now(), vals[2], topic, *fields.values()]
        sql = f"INSERT INTO videos ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"
        cur = self.conn.execute(sql, vals)
        vid = cur.lastrowid
        log.audit("video_created", video_id=vid, topic=topic)
        return vid

    def get_video(self, vid: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM videos WHERE id=?", (vid,))

    def update_video(self, vid: int, **fields):
        if not fields:
            return
        for k in ("hashtags", "script_json"):
            if isinstance(fields.get(k), (list, dict, tuple)):
                fields[k] = json.dumps(fields[k], ensure_ascii=False)
        if "status" in fields and fields["status"] not in VALID_STATUS:
            raise ValueError(f"Galat status '{fields['status']}'. Allowed: {VALID_STATUS}")
        sets = ",".join(f"{k}=?" for k in fields) + ",updated_ts=?"
        self.conn.execute(f"UPDATE videos SET {sets} WHERE id=?",
                          [*fields.values(), now(), vid])

    def set_status(self, vid: int, status: str, note: str | None = None):
        self.update_video(vid, status=status, **({"notes": note} if note else {}))
        log.audit("status_change", video_id=vid, status=status, note=note)

    def videos_by_status(self, status: str, limit: int = 50) -> list[sqlite3.Row]:
        return self.q("SELECT * FROM videos WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit))

    def recent_videos(self, n: int = 20) -> list[sqlite3.Row]:
        return self.q("SELECT * FROM videos ORDER BY id DESC LIMIT ?", (n,))

    # ---- rotation helpers (Section 5: voice/template repeat nahi hone chahiye) ----
    def recent_values(self, column: str, n: int = 5) -> list[str]:
        """Pichhle n videos mein iss column ki values — rotation check ke liye."""
        if column not in ("hook_type", "voice_id", "template_id"):
            raise ValueError("Sirf hook_type / voice_id / template_id allowed hai")
        rows = self.q(
            f"SELECT {column} AS v FROM videos WHERE {column} IS NOT NULL ORDER BY id DESC LIMIT ?", (n,))
        return [r["v"] for r in rows]

    def pick_rotated(self, column: str, options: list[str], avoid_last: int = 4) -> str:
        """Aisi value chuno jo pichhle `avoid_last` videos mein use na hui ho."""
        recent = set(self.recent_values(column, avoid_last))
        fresh = [o for o in options if o not in recent]
        return (fresh or options)[0]

    # ---------- metrics ----------
    def save_metrics(self, video_id: int, platform: str, window: str, **m):
        raw = m.pop("raw_json", None)
        keys = ["views", "likes", "comments", "shares", "saves",
                "avg_pct", "ret_1s", "ret_3s", "replays"]
        vals = [m.get(k, 0) if k not in ("avg_pct", "ret_1s", "ret_3s") else m.get(k) for k in keys]
        self.conn.execute(
            f"INSERT OR REPLACE INTO metrics (video_id,platform,window,ts,{','.join(keys)},raw_json)"
            f" VALUES (?,?,?,?,{','.join('?' * len(keys))},?)",
            [video_id, platform, window, now(), *vals,
             json.dumps(raw, ensure_ascii=False) if raw is not None else None])

    def get_metrics(self, video_id: int, window: str | None = None) -> list[sqlite3.Row]:
        if window:
            return self.q("SELECT * FROM metrics WHERE video_id=? AND window=?", (video_id, window))
        return self.q("SELECT * FROM metrics WHERE video_id=?", (video_id,))

    # ---------- experiments ----------
    def create_experiment(self, variable: str, hypothesis: str, arm_a: str, arm_b: str,
                          min_per_arm: int = 5) -> int:
        running = self.one("SELECT id FROM experiments WHERE status='running'")
        if running:
            # Section 6: "Ek time pe ek variable test karo"
            raise ValueError(f"Experiment #{running['id']} pehle se chal raha hai. "
                             f"Pehle usse conclude karo — ek time pe ek hi variable.")
        cur = self.conn.execute(
            "INSERT INTO experiments (created_ts,variable,hypothesis,arm_a,arm_b,min_per_arm)"
            " VALUES (?,?,?,?,?,?)", (now(), variable, hypothesis, arm_a, arm_b, min_per_arm))
        log.audit("experiment_created", exp_id=cur.lastrowid, variable=variable)
        return cur.lastrowid

    def running_experiment(self) -> sqlite3.Row | None:
        return self.one("SELECT * FROM experiments WHERE status='running' ORDER BY id DESC")

    def conclude_experiment(self, exp_id: int, result: dict):
        self.conn.execute("UPDATE experiments SET status='concluded',result_json=?,concluded_ts=? WHERE id=?",
                          (json.dumps(result, ensure_ascii=False), now(), exp_id))
        log.audit("experiment_concluded", exp_id=exp_id, **{"winner": result.get("winner")})

    # ---------- learnings ----------
    def add_learning(self, variable: str, winner: str, loser: str, lift_pct: float,
                     sample_size: int, confidence: str = "low",
                     source_exp: int | None = None, note: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO learnings (ts,variable,winner,loser,lift_pct,sample_size,confidence,source_exp,note)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (now(), variable, winner, loser, lift_pct, sample_size, confidence, source_exp, note))
        log.audit("learning_saved", variable=variable, winner=winner, lift=lift_pct)
        return cur.lastrowid

    def active_learnings(self, variable: str | None = None) -> list[sqlite3.Row]:
        """Writer/ArtDirector/Voice har run se pehle isse padhte hain."""
        self.expire_old_learnings()
        if variable:
            return self.q("SELECT * FROM learnings WHERE still_valid=1 AND variable=? ORDER BY id DESC",
                          (variable,))
        return self.q("SELECT * FROM learnings WHERE still_valid=1 ORDER BY id DESC")

    def expire_old_learnings(self, days: int = 90):
        """Section 7: 90 din purani learning ka confidence downgrade karo."""
        cutoff = f"-{days} days"
        self.conn.execute(
            "UPDATE learnings SET confidence=CASE confidence WHEN 'high' THEN 'medium'"
            " WHEN 'medium' THEN 'low' ELSE 'low' END,"
            " note=COALESCE(note,'')||' [auto-downgraded: 90+ din purani]'"
            " WHERE still_valid=1 AND confidence!='low' AND ts < datetime('now', ?)"
            " AND note NOT LIKE '%auto-downgraded%'", (cutoff,))

    # ---------- events ----------
    def log_event(self, kind: str, agent: str = "system", video_id: int | None = None, **payload):
        self.conn.execute("INSERT INTO events (ts,agent,kind,video_id,payload) VALUES (?,?,?,?,?)",
                          (now(), agent, kind, video_id, json.dumps(payload, ensure_ascii=False, default=str)))

    # ---------- dashboard ----------
    def dashboard_summary(self) -> dict:
        counts = {r["status"]: r["n"] for r in self.q("SELECT status, COUNT(*) n FROM videos GROUP BY status")}
        exp = self.running_experiment()
        return {
            "videos_by_status": counts,
            "pending_approval": counts.get("validated", 0),
            "published_total": counts.get("published", 0),
            "running_experiment": dict(exp) if exp else None,
            "active_learnings": len(self.active_learnings()),
        }


if __name__ == "__main__":
    with DB() as db:
        print("DB ready:", db.path)
        print(json.dumps(db.dashboard_summary(), indent=2, ensure_ascii=False))
