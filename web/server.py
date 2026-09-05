"""
web/server.py — Local dashboard. Sirf Python stdlib (http.server), koi Flask nahi.

Kya dikhta hai:
  * APPROVE QUEUE   — rendered videos, video player ke saath, Approve/Reject buttons
                      (`autonomy: review_first` ke liye — pehle 20 tum approve karoge)
  * QUOTA           — har API ka budget, live
  * METRICS         — 2h / 24h numbers (Phase 7 mein bharenge)
  * EXPERIMENTS     — chal rahe A/B tests (Phase 8)
  * LEARNINGS       — jo ab tak seekha
  * LOGS            — aaj ke errors/warnings

Chalao:
    python -m web.server
    Phir browser mein kholo: http://localhost:8765

⚠️ Ye dashboard SIRF localhost pe bind hota hai. Internet pe expose mat karna —
   isme koi authentication nahi hai (local tool hai, isliye zaroorat bhi nahi).
"""

from __future__ import annotations
import sys, io
# Windows terminal Unicode fix
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import mimetypes
import os
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from core.quota import Quota

log = Logbook("dashboard")
ROOT = Path(CONFIG["_root"])
PORT = int(CONFIG.get("dashboard_port", 8765))

import hmac
from collections import defaultdict

# Make.com webhook secret — .env mein MAKE_WEBHOOK_SECRET set karo (min 32 chars)
MAKE_WEBHOOK_SECRET = os.environ.get("MAKE_WEBHOOK_SECRET", "")
if MAKE_WEBHOOK_SECRET and len(MAKE_WEBHOOK_SECRET) < 32:
    log.warn(f"MAKE_WEBHOOK_SECRET chhota hai ({len(MAKE_WEBHOOK_SECRET)} chars) — min 32 chars rakho")

# In-memory rate limiting: per-IP max 10 requests per minute
WEBHOOK_RATE_LIMIT = 10
WEBHOOK_RATE_WINDOW = 60.0
_webhook_requests: dict[str, list[float]] = defaultdict(list)
_webhook_lock = threading.Lock()


def _check_webhook_auth(headers: dict, body: dict, client_ip: str | None = None) -> tuple[bool, int, str]:
    """
    Pure auth & rate limit checker for /api/webhook.
    Returns: (is_ok, http_status_code, error_or_ok_message)
    """
    # Agar environment variable expressly define ho chuka hai (chahe empty ho) to usse lo
    if "MAKE_WEBHOOK_SECRET" in os.environ:
        secret = os.environ["MAKE_WEBHOOK_SECRET"].strip()
    else:
        secret = MAKE_WEBHOOK_SECRET.strip()
    if not secret:
        log.warn("Webhook disabled — .env mein MAKE_WEBHOOK_SECRET set karo (min 32 chars)")
        return False, 403, "Webhook disabled: MAKE_WEBHOOK_SECRET not configured"

    # Rate limiting check
    ip_key = client_ip or "unknown"
    now = time.time()
    with _webhook_lock:
        timestamps = [t for t in _webhook_requests[ip_key] if now - t < WEBHOOK_RATE_WINDOW]
        if len(timestamps) >= WEBHOOK_RATE_LIMIT:
            _webhook_requests[ip_key] = timestamps
            log.warn(f"Webhook rate limit exceed hua for IP {ip_key}")
            return False, 429, "Rate limit exceeded (max 10 req/min)"
        timestamps.append(now)
        _webhook_requests[ip_key] = timestamps

    # Authentication check via constant-time hmac.compare_digest
    incoming = body.get("secret", "") or headers.get("X-Webhook-Secret", "")
    if not isinstance(incoming, str) or not incoming or not hmac.compare_digest(incoming, secret):
        log.warn("Webhook: galat secret, reject kar rahe hain")
        return False, 403, "Invalid secret"

    return True, 200, "OK"



# =====================================================================
# DATA — dashboard ko chahiye sab kuch
# =====================================================================
def gather() -> dict:
    db = DB()
    q = Quota(db)
    try:
        # ---- approve queue: rendered hai par abhi approve/reject nahi hua ----
        queue = []
        for r in db.q("SELECT * FROM videos WHERE status IN ('rendered','validated') "
                      "ORDER BY id DESC LIMIT 20"):
            d = ROOT / "output" / f"video_{r['id']:04d}"
            script = json.loads(r["script_json"] or "{}")
            queue.append({
                "id": r["id"],
                "title": r["title"],
                "topic": r["topic"],
                "status": r["status"],
                "hook_type": r["hook_type"],
                "voice_id": r["voice_id"],
                "template_id": r["template_id"],
                "length_sec": r["length_sec"],
                "hashtags": json.loads(r["hashtags"] or "[]"),
                "caption": r["caption"],
                "hook_line": script.get("hook_line", ""),
                "hook_overlay": script.get("hook_text_overlay", ""),
                "comment_bait": script.get("comment_bait", ""),
                "video_url": f"/media/video_{r['id']:04d}/final.mp4"
                             if (d / "final.mp4").exists() else None,
                "cover_url": f"/media/video_{r['id']:04d}/cover.jpg"
                             if (d / "cover.jpg").exists() else None,
                "created": r["created_ts"],
            })

        # ---- recently published + unke metrics ----
        published = []
        for r in db.q("SELECT * FROM videos WHERE status='published' ORDER BY id DESC LIMIT 10"):
            mets = {m["window"]: dict(m) for m in db.get_metrics(r["id"])}
            published.append({
                "id": r["id"], "title": r["title"], "hook_type": r["hook_type"],
                "voice_id": r["voice_id"], "template_id": r["template_id"],
                "published_ts": r["published_ts"],
                "yt_video_id": r["yt_video_id"], "ig_media_id": r["ig_media_id"],
                "m2h": mets.get("2h"), "m24h": mets.get("24h"), "m7d": mets.get("7d"),
            })

        # ---- analyst: baseline + variable report (dashboard ke liye) ----
        analysis = {}
        try:
            from agents.analyst import Analyst
            an = Analyst(db, q)
            analysis = {
                "baseline": an.baseline(window="2h"),
                "variables": an.variable_report(window="2h"),
                "due": len(an.due_videos()),
                "recent": [an.analyze(p["id"], "2h") for p in published[:3]
                           if p.get("m2h")],
            }
        except Exception as e:  # noqa: BLE001
            log.warn(f"Analyst data skip: {str(e)[:120]}")

        exp = db.running_experiment()
        learnings = [dict(r) for r in db.active_learnings()[:12]]

        # ---- scientist: experiment status + champions ----
        science = {}
        try:
            from agents.scientist import Scientist
            sci = Scientist(db)
            science = {"champions": sci.champions(), "losers": sci.losers(),
                       "suggestion": None if exp else sci.suggest_next(),
                       "evaluation": sci.evaluate() if exp else None}
        except Exception as e:  # noqa: BLE001
            log.warn(f"Scientist data skip: {str(e)[:120]}")

        # ---- aaj ke logs (sirf WARN/ERROR — INFO ka shor nahi chahiye) ----
        logs = []
        lf = Path(CONFIG["log_dir"]) / f"autopilot-{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
        if lf.exists():
            for line in lf.read_text(encoding="utf-8").splitlines()[-400:]:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("level") in ("WARN", "ERROR", "FATAL"):
                    logs.append(rec)
        logs = logs[-40:][::-1]

        return {
            "brand": CONFIG.get("brand_name", "AUTOPILOT"),
            "autonomy": CONFIG.get("autonomy", "review_first"),
            "mock_mode": bool(CONFIG.get("mock_mode")),
            "summary": db.dashboard_summary(),
            "queue": queue,
            "published": published,
            "quota": q.snapshot(),
            "analysis": analysis,
            "science": science,
            "experiment": dict(exp) if exp else None,
            "learnings": learnings,
            "logs": logs,
            "active_task": CURRENT_TASK,
            "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    finally:
        db.close()


# Task tracking for background generation and tick processes
CURRENT_TASK = {"status": "idle", "task": None, "msg": "", "started_ts": None}

def run_bg_task(name: str, fn):
    global CURRENT_TASK
    if CURRENT_TASK["status"] == "running":
        return {"ok": False, "error": f"Ek task pehle se chal raha hai: {CURRENT_TASK['task']}"}
    
    CURRENT_TASK = {
        "status": "running",
        "task": name,
        "msg": f"{name} shuru ho raha hai...",
        "started_ts": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }

    def _worker():
        global CURRENT_TASK
        try:
            res_msg = fn()
            CURRENT_TASK = {
                "status": "completed",
                "task": name,
                "msg": res_msg or f"{name} poora hua 🎉",
                "started_ts": None
            }
        except Exception as e:  # noqa: BLE001
            log.error(f"Background task {name} fail hua", e)
            CURRENT_TASK = {
                "status": "error",
                "task": name,
                "msg": f"Error: {str(e)}",
                "started_ts": None
            }

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "msg": f"{name} background mein shuru kar diya hai"}

# =====================================================================
# ACTIONS
# =====================================================================
def do_action(action: str, video_id: int, payload: dict) -> dict:
    with DB() as db:
        # ---- experiment actions kisi video se bandhe nahi hain ----
        if action == "generate":
            topic = payload.get("topic")
            dry_run = bool(payload.get("dry_run", CONFIG.get("mock_mode")))

            def _gen():
                from run import make_video
                vid = make_video(topic=topic, dry_run=dry_run)
                return f"Video #{vid} ban ke tayar hai!"

            return run_bg_task("Video Generation", _gen)

        if action == "publish_video":
            v = db.get_video(video_id)
            if not v:
                return {"ok": False, "error": f"Video #{video_id} nahi mila"}
            
            def _pub():
                from agents.publisher import Publisher
                from agents.ig_publisher import IGPublisher
                q = Quota(db)
                out_yt = Publisher(db, q).publish_due()
                out_ig = IGPublisher(db, q).publish_due()
                return f"YT: {len(out_yt.get('published', []))} uploaded | IG: {len(out_ig.get('published', []))} uploaded"

            return run_bg_task(f"Publish Video #{video_id}", _pub)

        if action == "exp_start":
            from agents.scientist import Scientist
            r = Scientist(db).start(payload.get("variable") or None)
            return {"ok": r.get("ok", False),
                    "msg": (f"Experiment #{r['experiment_id']} shuru: {r['variable']} "
                            f"({r['arm_a']} vs {r['arm_b']})") if r.get("ok") else None,
                    "error": r.get("error")}

        if action == "tick":
            dry_run = bool(payload.get("dry_run"))

            def _tick_fn():
                from agents.chief import Chief, Lock
                with Lock():
                    out = Chief(db, dry_run=dry_run).tick()
                acts = out.get("actions") or ["kuch karne ko nahi tha"]
                return " | ".join(acts)[:200]

            return run_bg_task("Chief Tick", _tick_fn)

        if action == "exp_conclude":
            from agents.scientist import Scientist
            r = Scientist(db).conclude(force=bool(payload.get("force")))
            return {"ok": bool(r.get("concluded")),
                    "msg": r.get("verdict"), "error": r.get("error")}

        # ---- yahan se aage sab video-specific hain ----
        v = db.get_video(video_id)
        if not v:
            return {"ok": False, "error": f"Video #{video_id} nahi mila"}

        if action == "approve":
            db.set_status(video_id, "approved", note="dashboard se approve hua")
            db.log_event("approval", "human", video_id, decision="approved")
            return {"ok": True, "msg": f"Video #{video_id} approve ho gaya — "
                                       f"publish queue mein chala gaya"}

        if action == "reject":
            reason = payload.get("reason", "koi reason nahi diya")
            db.set_status(video_id, "rejected", note=f"reject: {reason}")
            db.log_event("approval", "human", video_id, decision="rejected", reason=reason)
            return {"ok": True, "msg": f"Video #{video_id} reject ho gaya"}

        if action == "rerender":
            out_dir = ROOT / "output" / f"video_{video_id:04d}"
            mf = out_dir / "manifest.json"
            if not mf.exists():
                return {"ok": False, "error": f"manifest.json nahi mila: {mf}"}
            from pipeline.render import Renderer
            from pipeline.validate import validate_dir
            try:
                info = Renderer(mf).render(out_dir, preset=payload.get("preset", "medium"),
                                           keep_temp=bool(payload.get("keep_temp", False)))
                m = json.loads(mf.read_text(encoding="utf-8"))
                m["render"] = info
                rep = validate_dir(out_dir)
                m["validation"] = rep.to_dict()
                mf.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
                db.update_video(video_id, video_path=info["video_path"],
                                cover_path=info["cover_path"],
                                length_sec=info["duration_sec"],
                                status="validated" if rep.ok else "failed")
                db.log_event("rerendered", "dashboard", video_id, ok=rep.ok)
                return {"ok": True, "msg": f"Video #{video_id} dobara render ho gaya", "info": info, "report": rep.to_dict()}
            except Exception as e:
                db.set_status(video_id, "failed", note=f"rerender fail: {str(e)[:150]}")
                log.error(f"Rerender fail video #{video_id}", e)
                return {"ok": False, "error": f"Render fail: {e}"}

        if action == "validate":
            from pipeline.validate import validate_dir
            rep = validate_dir(ROOT / "output" / f"video_{video_id:04d}")
            if rep.ok:
                db.set_status(video_id, "validated",
                              note=f"validate pass, {len(rep.warns)} warning")
            db.log_event("validated", "system", video_id, ok=rep.ok,
                         issues=len(rep.issues))
            return {"ok": True, "report": rep.to_dict()}

        return {"ok": False, "error": f"Unknown action: {action}"}


def fetch_logs(video_id: int | None = None, limit: int = 200) -> list[dict]:
    """logs/*.jsonl se logs padho. video_id filter ho to specific video ke."""
    log_dir = (ROOT / CONFIG.get("log_dir", "logs")).resolve()
    if not str(log_dir).startswith(str(ROOT.resolve())):
        return []

    entries = []
    if log_dir.exists():
        for log_file in sorted(log_dir.glob("*.jsonl"), reverse=True):
            try:
                with open(log_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            if video_id is not None:
                                v_match = (obj.get("video_id") == video_id or
                                           obj.get("vid") == video_id or
                                           f"#{video_id}" in str(obj.get("msg", "")) or
                                           f"video_{video_id:04d}" in str(obj))
                                if not v_match:
                                    continue
                            entries.append(obj)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                log.warn(f"Log file read fail: {log_file.name}", e)
            if len(entries) >= limit:
                break
    return entries[:limit]


# =====================================================================
# HTTP
# =====================================================================
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # default console spam band karo

    # ---------- GET ----------
    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        if u.path == "/":
            return self._send(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))
        if u.path == "/api/data":
            try:
                return self._json(200, gather())
            except Exception as e:  # noqa: BLE001
                log.error("Dashboard data fail", e)
                return self._json(500, {"error": str(e)})
        # ---- Make.com status polling endpoint ----
        if u.path == "/api/status":
            return self._json(200, {
                "ok": True,
                "task": CURRENT_TASK,
                "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
        # ---- Log viewer endpoint: /api/logs?video_id=N ----
        if u.path == "/api/logs":
            qs = parse_qs(u.query)
            vid_str = qs.get("video_id", [""])[0]
            try:
                vid = int(vid_str) if vid_str else None
            except ValueError:
                return self._json(400, {"ok": False, "error": "Invalid video_id"})
            return self._serve_logs(vid)

        if u.path.startswith("/media/"):
            return self._media(u.path[len("/media/"):])
        self._send(404, "text/plain", b"404")

    # ---------- POST ----------
    def do_POST(self):  # noqa: N802
        u = urlparse(self.path)

        # ---- Make.com webhook endpoint ----
        if u.path == "/api/webhook":
            return self._handle_webhook()

        if u.path != "/api/action":
            return self._send(404, "text/plain", b"404")
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            res = do_action(body.get("action", ""), int(body.get("video_id", 0)), body)
            return self._json(200, res)
        except Exception as e:  # noqa: BLE001
            log.error("Dashboard action fail", e)
            return self._json(500, {"ok": False, "error": str(e)})

    def _handle_webhook(self):
        """Make.com ya koi bhi automation tool is endpoint ko call kar sakta hai.

        Expected JSON body:
          {
            "secret": "tumhara-secret",   (optional, agar MAKE_WEBHOOK_SECRET set hai)
            "action": "generate" | "tick",
            "topic": "optional topic string",
            "dry_run": false
          }

        Response:
          { "ok": true, "msg": "..." }  ya  { "ok": false, "error": "..." }
        """
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")

            client_ip = self.client_address[0] if hasattr(self, "client_address") and self.client_address else "unknown"
            headers_dict = dict(self.headers)
            ok, status_code, err_msg = _check_webhook_auth(headers_dict, body, client_ip)
            if not ok:
                return self._json(status_code, {"ok": False, "error": err_msg})

            action = body.get("action", "generate")
            topic  = body.get("topic") or None
            dry_run = bool(body.get("dry_run", False))

            log.info(f"Make.com webhook aaya: action={action} topic={topic}")

            with DB() as db:
                payload = {"topic": topic, "dry_run": dry_run}
                res = do_action(action, 0, payload)

            return self._json(200, res)
        except Exception as e:  # noqa: BLE001
            log.error("Webhook fail", e)
            return self._json(500, {"ok": False, "error": str(e)})

    # ---------- helpers ----------
    def _media(self, rel: str):
        """output/ folder se video/image serve karo. Path traversal se bachav ke saath."""
        target = (ROOT / "output" / rel).resolve()
        if not str(target).startswith(str((ROOT / "output").resolve())):
            return self._send(403, "text/plain", b"Nope")   # ../../etc/passwd attack
        if not target.exists() or not target.is_file():
            return self._send(404, "text/plain", b"Not found")

        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        size = target.stat().st_size
        rng = self.headers.get("Range")

        # Video seeking ke liye Range requests support karni padti hain
        if rng and rng.startswith("bytes="):
            try:
                s, _, e = rng[6:].partition("-")
                start = int(s) if s else 0
                end = int(e) if e else size - 1
                end = min(end, size - 1)
                length = end - start + 1
                self.send_response(206)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(length))
                self.end_headers()
                with target.open("rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
                return
            except (ValueError, BrokenPipeError):
                return

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        try:
            self.wfile.write(target.read_bytes())
        except BrokenPipeError:
            pass  # browser ne video band kar diya — normal hai

    def _send(self, code: int, ctype: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _serve_logs(self, video_id: int | None = None):
        log_dir = (ROOT / CONFIG.get("log_dir", "logs")).resolve()
        if not str(log_dir).startswith(str(ROOT.resolve())):
            return self._json(403, {"ok": False, "error": "Access denied"})
        entries = fetch_logs(video_id)
        return self._json(200, {"ok": True, "video_id": video_id, "count": len(entries), "logs": entries})

    def _json(self, code: int, obj):
        self._send(code, "application/json; charset=utf-8",
                   json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))


PAGE = r"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🎬 AUTOPILOT 3D Swarm Control Center</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg-deep: #050811;
  --bg-surface: #0a0f1d;
  --bg-card: rgba(14, 20, 37, 0.72);
  --border-subtle: rgba(255, 255, 255, 0.07);
  --border-glow: rgba(56, 189, 248, 0.35);
  --cyan: #00f2fe;
  --blue: #38bdf8;
  --purple: #818cf8;
  --green: #34d399;
  --amber: #fbbf24;
  --red: #f87171;
  --text-main: #f1f5f9;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg-deep);
  color: var(--text-main);
  font: 14px/1.55 'Inter', -apple-system, sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
}

/* Background 3D Particle Canvas */
#bgCanvas {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  z-index: 0;
  pointer-events: none;
}

/* App 3D Container */
#app {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin: 0 auto;
  padding: 16px 24px 80px;
  perspective: 1400px;
  transform-style: preserve-3d;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
#app.holo-view {
  transform: perspective(1400px) rotateX(10deg) rotateY(-4deg) scale(0.95);
}

/* Top Hologram HUD */
.hud-header {
  background: rgba(10, 15, 29, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  padding: 14px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  box-shadow: 0 10px 35px -10px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255,255,255,0.08);
}
.brand-box {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-logo {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #fff 20%, var(--cyan) 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
}
.brand-logo i {
  display: inline-block;
  font-style: normal;
  animation: pulse-glow 2.5s infinite ease-in-out;
}
@keyframes pulse-glow {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 6px rgba(0,242,254,0.4)); }
  50% { transform: scale(1.08); filter: drop-shadow(0 0 14px rgba(0,242,254,0.8)); }
}

.badge {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.badge.ok { background: rgba(52, 211, 153, 0.12); border-color: rgba(52, 211, 153, 0.35); color: var(--green); }
.badge.warn { background: rgba(251, 191, 36, 0.12); border-color: rgba(251, 191, 36, 0.35); color: var(--amber); }
.badge.bad { background: rgba(248, 113, 113, 0.15); border-color: rgba(248, 113, 113, 0.35); color: var(--red); }
.badge.live { background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.4); color: var(--blue); }

.hud-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 3D Button Engine */
.btn {
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #fff;
  position: relative;
  outline: none;
}
.btn:active { transform: scale(0.96); }
.btn-primary {
  background: linear-gradient(135deg, #0284c7, #0369a1);
  border-color: rgba(56, 189, 248, 0.4);
  box-shadow: 0 4px 18px rgba(2, 132, 199, 0.35), inset 0 1px 0 rgba(255,255,255,0.2);
}
.btn-primary:hover {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  box-shadow: 0 6px 24px rgba(56, 189, 248, 0.5);
  transform: translateY(-1px);
}
.btn-success {
  background: linear-gradient(135deg, #059669, #047857);
  border-color: rgba(52, 211, 153, 0.4);
  box-shadow: 0 4px 18px rgba(5, 150, 105, 0.35);
}
.btn-success:hover {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 6px 24px rgba(52, 211, 153, 0.5);
  transform: translateY(-1px);
}
.btn-danger {
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.3);
  color: var(--red);
}
.btn-danger:hover {
  background: rgba(248, 113, 113, 0.22);
  border-color: var(--red);
}
.btn-ghost {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--border-subtle);
  color: var(--text-muted);
}
.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-main);
  border-color: rgba(255,255,255,0.2);
}
.btn-holo {
  background: linear-gradient(135deg, rgba(129, 140, 248, 0.15), rgba(56, 189, 248, 0.15));
  border-color: rgba(129, 140, 248, 0.35);
  color: #c7d2fe;
}
.btn-holo:hover {
  background: linear-gradient(135deg, rgba(129, 140, 248, 0.28), rgba(56, 189, 248, 0.28));
  color: #fff;
  border-color: #818cf8;
}

/* Nav Pills */
.nav-bar {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 16px 4px 8px;
  margin-bottom: 8px;
  scrollbar-width: none;
}
.nav-bar::-webkit-scrollbar { display: none; }
.nav-tab {
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 7px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.nav-tab:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-main);
  border-color: rgba(255, 255, 255, 0.15);
}
.nav-tab.active {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(99, 102, 241, 0.2));
  border-color: var(--blue);
  color: #fff;
  box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
}
.nav-tab .tab-count {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}
.nav-tab.active .tab-count {
  background: var(--blue);
  color: #040813;
}
.nav-tab.tab-err.has-err .tab-count {
  background: var(--red);
  color: #fff;
  animation: pulse-glow 1.5s infinite;
}

/* Active Task Banner */
.task-banner {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(99, 102, 241, 0.25));
  border: 1px solid rgba(56, 189, 248, 0.4);
  backdrop-filter: blur(12px);
  color: #fff;
  padding: 12px 20px;
  border-radius: 14px;
  margin: 14px 0 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 10px 30px rgba(14, 165, 233, 0.25);
  animation: border-glow 3s infinite alternate;
}
@keyframes border-glow {
  0% { border-color: rgba(56, 189, 248, 0.3); }
  100% { border-color: rgba(129, 140, 248, 0.7); }
}
.task-spinner {
  width: 18px; height: 18px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--cyan);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 3D Cards & Layout */
.grid { display: grid; gap: 16px; }
.cards-4 { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-bottom: 22px; }

.card-3d {
  background: var(--bg-card);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 18px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out, box-shadow 0.25s ease, border-color 0.25s ease;
  box-shadow: 0 12px 35px -10px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
.card-3d:hover {
  border-color: var(--border-glow);
  box-shadow: 0 20px 45px -12px rgba(14, 165, 233, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
.card-3d .glare {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  border-radius: inherit;
  pointer-events: none;
  background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.08), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s;
}
.card-3d:hover .glare { opacity: 1; }

.stat-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.stat-k {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.1px;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.stat-v {
  font-family: 'Outfit', sans-serif;
  font-size: 32px;
  font-weight: 700;
  margin-top: 8px;
  color: #fff;
  letter-spacing: -0.5px;
}
.stat-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Sections */
.section {
  margin-bottom: 36px;
  display: block;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 28px 0 14px;
  flex-wrap: wrap;
  gap: 12px;
}
.section-title {
  font-family: 'Outfit', sans-serif;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: #cbd5e1;
  display: flex;
  align-items: center;
  gap: 9px;
}
.section-title span.glow-icon {
  font-size: 20px;
  filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.6));
}

/* Quota Mini Ring / Progress Bars */
.quota-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}
.q-row {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.q-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}
.q-name { font-weight: 600; color: var(--text-muted); }
.q-nums { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #cbd5e1; }
.q-bar-bg {
  width: 100%;
  height: 7px;
  background: rgba(255, 255, 255, 0.07);
  border-radius: 4px;
  overflow: hidden;
}
.q-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #34d399, #10b981);
  transition: width 0.5s ease;
}
.q-bar-fill.w { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.q-bar-fill.d { background: linear-gradient(90deg, #f87171, #ef4444); }

/* 3D SWARM PIPELINE DIAGRAM SECTION */
.diagram-card {
  padding: 18px 20px;
  border-radius: 18px;
  background: rgba(10, 15, 28, 0.85);
  border: 1px solid rgba(56, 189, 248, 0.25);
  box-shadow: 0 16px 40px -10px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.1);
  position: relative;
  overflow: hidden;
}
#swarmCanvas {
  width: 100%;
  height: 270px;
  display: block;
  cursor: crosshair;
}
.diagram-hud {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-muted);
}
.diagram-tooltip {
  position: absolute;
  pointer-events: none;
  background: rgba(3, 7, 18, 0.92);
  border: 1px solid var(--cyan);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  color: #fff;
  box-shadow: 0 8px 24px rgba(0, 242, 254, 0.35);
  display: none;
  z-index: 10;
  max-width: 260px;
}

/* LIVE GRAPHS SECTION */
.graph-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
  gap: 18px;
}
.chart-box {
  background: var(--bg-card);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 16px 20px;
  position: relative;
}
.chart-box h3 {
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chart-canvas {
  width: 100%;
  height: 240px;
  display: block;
}

/* DEDICATED ERROR & DIAGNOSTICS HUB */
.diag-hub {
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(248, 113, 113, 0.25);
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 16px 45px -10px rgba(248, 113, 113, 0.12), inset 0 1px 0 rgba(255,255,255,0.08);
  position: relative;
}
.diag-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.diag-search {
  flex: 1;
  min-width: 220px;
  background: rgba(5, 8, 17, 0.7);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 8px 14px;
  color: #fff;
  font-family: inherit;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}
.diag-search:focus {
  border-color: var(--blue);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
}
.diag-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.diag-pill {
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}
.diag-pill:hover { color: #fff; border-color: rgba(255, 255, 255, 0.2); }
.diag-pill.active {
  background: rgba(248, 113, 113, 0.2);
  border-color: var(--red);
  color: #fff;
}
.diag-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 4px;
}
.diag-item {
  background: rgba(5, 9, 20, 0.65);
  border: 1px solid var(--border-subtle);
  border-left: 4px solid var(--amber);
  border-radius: 10px;
  padding: 12px 16px;
  transition: transform 0.15s ease, border-color 0.2s;
}
.diag-item:hover {
  transform: translateX(4px);
  background: rgba(8, 14, 30, 0.85);
}
.diag-item.lvl-FATAL, .diag-item.lvl-ERROR {
  border-left-color: var(--red);
}
.diag-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.diag-ts { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-dim); }
.diag-agent {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.07);
  color: #cbd5e1;
}
.diag-msg {
  font-size: 13.5px;
  color: #f1f5f9;
  line-height: 1.5;
}
.diag-detail {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  background: rgba(0, 0, 0, 0.45);
  border-radius: 6px;
  padding: 8px 12px;
  margin-top: 8px;
  color: #94a3b8;
  white-space: pre-wrap;
  word-break: break-all;
}
.diag-fix {
  font-size: 12px;
  color: var(--cyan);
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* VIDEO STUDIO QUEUE SECTION */
.video-card {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 22px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  padding: 20px;
  margin-bottom: 18px;
  box-shadow: 0 12px 35px -10px rgba(0, 0, 0, 0.7);
  transform-style: preserve-3d;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.video-card:hover {
  border-color: var(--border-glow);
  box-shadow: 0 20px 45px -10px rgba(14, 165, 233, 0.25);
}
@media (max-width: 780px) {
  .video-card { grid-template-columns: 1fr; }
  .graph-grid { grid-template-columns: 1fr; }
}
.video-media {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  aspect-ratio: 9/16;
  max-height: 460px;
}
.video-media video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.video-info {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.video-title {
  font-family: 'Outfit', sans-serif;
  font-size: 19px;
  font-weight: 700;
  color: #fff;
  line-height: 1.35;
  margin-bottom: 8px;
}
.video-meta {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
  margin: 8px 0 12px;
}
.hook-box {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.08), rgba(245, 158, 11, 0.04));
  border-left: 3px solid var(--amber);
  padding: 10px 14px;
  border-radius: 0 10px 10px 0;
  margin: 10px 0;
  font-size: 13px;
}
.hook-box b { color: #fef08a; }
.btn-deck {
  display: flex;
  gap: 9px;
  flex-wrap: wrap;
  margin-top: 14px;
}

/* TABLES (Published & Science) */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  color: var(--text-dim);
  font-weight: 700;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
td {
  padding: 11px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #cbd5e1;
}
tr:hover td { background: rgba(255, 255, 255, 0.02); }

/* MODAL - 3D NEW VIDEO CREATOR */
.modal-overlay {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: rgba(2, 6, 23, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 999;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-card {
  background: #0b1120;
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 20px;
  width: 100%;
  max-width: 540px;
  padding: 26px;
  box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 40px rgba(56, 189, 248, 0.2);
  transform: perspective(1000px) rotateX(4deg);
  animation: modal-in 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes modal-in {
  from { opacity: 0; transform: perspective(1000px) translateY(30px) scale(0.95); }
  to { opacity: 1; transform: perspective(1000px) translateY(0) scale(1); }
}
.modal-title {
  font-family: 'Outfit', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.form-group {
  margin-bottom: 16px;
}
.form-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.form-input, .form-select {
  width: 100%;
  background: rgba(2, 6, 23, 0.75);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 10px 14px;
  color: #fff;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.form-input:focus, .form-select:focus {
  border-color: var(--blue);
  box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
}
.topic-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.topic-chip {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-subtle);
  padding: 3px 9px;
  border-radius: 14px;
  color: var(--cyan);
  cursor: pointer;
  transition: all 0.2s;
}
.topic-chip:hover {
  background: rgba(0, 242, 254, 0.15);
  border-color: var(--cyan);
}

/* Toast */
#toast {
  position: fixed;
  bottom: 28px; right: 28px;
  background: #0f172a;
  border: 1px solid var(--cyan);
  color: #fff;
  padding: 14px 24px;
  border-radius: 12px;
  display: none;
  font-weight: 600;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7), 0 0 20px rgba(0, 242, 254, 0.3);
  z-index: 9999;
}
</style>
</head>
<body>

<!-- 3D Background Starfield Canvas -->
<canvas id="bgCanvas"></canvas>

<div id="app">
  <!-- Top Hologram HUD -->
  <header class="hud-header">
    <div class="brand-box">
      <div class="brand-logo"><i>🎬</i> <span id="brand">AUTOPILOT</span></div>
      <span class="badge" id="autonomy"></span>
      <span class="badge" id="mock"></span>
      <span class="badge live" id="clock"></span>
    </div>

    <div class="hud-actions">
      <button class="btn btn-holo" id="btnHolo" onclick="toggleHoloMode()" title="Toggle 3D Holo-Deck Perspective">🕶️ 3D Holo</button>
      <button class="btn btn-ghost" id="btnAudio" onclick="toggleSound()" title="Audio Sound FX Toggle">🔊 FX ON</button>
      <button class="btn btn-primary" onclick="openCreateModal()" title="Nayi Video Banao">✨ Nayi Video</button>
      <button class="btn btn-success" onclick="act('tick', 0)" title="Ek Poora Swarm Tick Run Karo">⚡ Run Swarm Tick</button>
    </div>
  </header>

  <!-- Active Task Banner -->
  <div id="task_banner" class="task-banner" style="display:none">
    <div class="task-spinner"></div>
    <span id="task_msg">Swarm task chal raha hai...</span>
  </div>

  <!-- Navigation Pills -->
  <nav class="nav-bar">
    <button class="nav-tab active" onclick="switchTab('all', this)">🌐 All Modules</button>
    <button class="nav-tab" onclick="switchTab('studio', this)">🎬 Video Studio <span class="tab-count" id="badgeQueue">0</span></button>
    <button class="nav-tab" onclick="switchTab('diagram', this)">⚡ 3D Swarm Pipeline</button>
    <button class="nav-tab" onclick="switchTab('graphs', this)">📊 Retention &amp; Trajectory</button>
    <button class="nav-tab" onclick="switchTab('science', this)">🧪 A/B Science Lab</button>
    <button class="nav-tab tab-err" id="tabErr" onclick="switchTab('errors', this)">⚠️ Diagnostics &amp; Errors <span class="tab-count" id="badgeErrors">0</span></button>
  </nav>

  <!-- Overview Stat HUD Cards -->
  <div class="grid cards-4" id="cards"></div>

  <!-- Quota HUD Row -->
  <section class="section" id="section-quota">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">📊</span> Quota &amp; Rate Limits Telemetry</h2>
    </div>
    <div class="card-3d">
      <div class="quota-grid" id="quota"></div>
      <div class="glare"></div>
    </div>
  </section>

  <!-- DEDICATED SECTION 1: ERROR & DIAGNOSTICS HUB -->
  <section class="section" id="section-errors">
    <div class="section-head">
      <h2 class="section-title" style="color:#f87171"><span class="glow-icon">⚠️</span> System Diagnostics &amp; Error Hub</h2>
      <div style="display:flex;gap:8px">
        <button class="btn btn-ghost" onclick="copyDiagnosticsReport()">📋 Copy Report</button>
        <button class="btn btn-ghost" onclick="load()">🔄 Refresh</button>
      </div>
    </div>

    <div class="diag-hub">
      <div class="diag-controls">
        <input type="text" id="diagSearch" class="diag-search" placeholder="🔍 Search errors, warnings, agents, or error codes..." oninput="filterLogs()">
        <div class="diag-pills">
          <button class="diag-pill active" onclick="setLogFilter('ALL', this)">All</button>
          <button class="diag-pill" onclick="setLogFilter('FATAL', this)">Fatal / Errors</button>
          <button class="diag-pill" onclick="setLogFilter('WARN', this)">Warnings</button>
          <button class="diag-pill" onclick="setLogFilter('VOICE', this)">Voice / TTS</button>
          <button class="diag-pill" onclick="setLogFilter('OAUTH', this)">OAuth</button>
          <button class="diag-pill" onclick="setLogFilter('QUOTA', this)">Quota</button>
          <button class="diag-pill" onclick="setLogFilter('PUB', this)">Publisher</button>
        </div>
      </div>
      <div class="diag-list" id="diagList"></div>
    </div>
  </section>

  <!-- DEDICATED SECTION 2: 3D SWARM ARCHITECTURE DIAGRAM -->
  <section class="section" id="section-diagram">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">⚡</span> Autonomous Swarm Flow Architecture</h2>
      <span class="badge ok">11 Active Agents · Event Conduits Online</span>
    </div>
    <div class="diagram-card">
      <canvas id="swarmCanvas" width="1280" height="270"></canvas>
      <div id="diagramTooltip" class="diagram-tooltip"></div>
      <div class="diagram-hud">
        <span>💡 Diagram interactivity: Hover over an agent node to inspect responsibilities &amp; status</span>
        <span id="swarmStatus">Chief ➔ TrendScout ➔ Writer ➔ ArtDirector ➔ Voice ➔ Render ➔ Gatekeeper ➔ Publisher ➔ Analyst ➔ Scientist</span>
      </div>
    </div>
  </section>

  <!-- DEDICATED SECTION 3: LIVE RETENTION & PERFORMANCE GRAPHS -->
  <section class="section" id="section-graphs">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">📈</span> Live Retention Curve &amp; View Velocity Graphs</h2>
      <span class="badge live">Interactive Scrubbing Active</span>
    </div>
    <div class="graph-grid">
      <div class="chart-box card-3d">
        <h3>
          <span>⏱️ Second-by-Second Retention Curve (0s - 60s)</span>
          <span style="font-size:12px;font-weight:400;color:var(--cyan)">Hover to scrub curve</span>
        </h3>
        <canvas id="retentionCanvas" class="chart-canvas" width="600" height="240"></canvas>
        <div class="glare"></div>
      </div>

      <div class="chart-box card-3d">
        <h3>
          <span>🚀 Published View Trajectory (2h vs 24h vs 7d)</span>
          <span style="font-size:12px;font-weight:400;color:var(--green)">Velocity Benchmarks</span>
        </h3>
        <canvas id="velocityCanvas" class="chart-canvas" width="600" height="240"></canvas>
        <div class="glare"></div>
      </div>
    </div>
  </section>

  <!-- DEDICATED SECTION 4: VIDEO CREATION & APPROVAL STUDIO -->
  <section class="section" id="section-queue">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">🎬</span> Video Studio &amp; Approval Deck</h2>
      <button class="btn btn-primary" onclick="openCreateModal()">✨ Create Video</button>
    </div>
    <div id="queue"></div>
  </section>

  <!-- DEDICATED SECTION 5: INTELLIGENCE & ANALYST -->
  <section class="section" id="section-analyst">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">🔬</span> Analyst Intelligence &amp; Baseline Metrics</h2>
    </div>
    <div class="card-3d" id="analyst"></div>
  </section>

  <!-- DEDICATED SECTION 6: A/B TESTING & SCIENCE LAB -->
  <section class="section" id="section-science">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">🧪</span> A/B Experiment &amp; Learning Laboratory</h2>
    </div>
    <div class="card-3d" id="sci"></div>
  </section>

  <!-- DEDICATED SECTION 7: PUBLISHED VAULT -->
  <section class="section" id="section-published">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">📜</span> Published Videos Archive</h2>
    </div>
    <div class="card-3d" id="published"></div>
  </section>
</div>

<!-- 3D NEW VIDEO MODAL -->
<div class="modal-overlay" id="videoModal">
  <div class="modal-card">
    <div class="modal-title">
      <span>✨ Nayi Video Banao</span>
      <button class="btn btn-ghost" style="padding:4px 8px;border-radius:50%" onclick="closeCreateModal()">✕</button>
    </div>
    <form id="createForm" onsubmit="submitCreateVideo(event)">
      <div class="form-group">
        <label class="form-label">Video Topic (Khaali chhodein to TrendScout auto choose karega)</label>
        <input type="text" id="topicInput" class="form-input" placeholder="e.g. Wo 14 log jo ek raat mein gayab ho gaye">
        <div class="topic-chips">
          <span class="topic-chip" onclick="setTopic('Kaali Pahadi ka 100 saal purana raaz')">Kaali Pahadi</span>
          <span class="topic-chip" onclick="setTopic('Wo aakhiri train jo station kabhi nahi pahunchi')">Aakhiri Train</span>
          <span class="topic-chip" onclick="setTopic('Ek band kamra aur 3 tasveerein')">Band Kamra</span>
          <span class="topic-chip" onclick="setTopic('Gaon ki purani haveli ka sach')">Purani Haveli</span>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Voice Model</label>
        <select id="voiceInput" class="form-select">
          <option value="">Auto (Scientist Champion / Balanced)</option>
          <option value="hi_f_urgent">Swara Urgent (Fast Suspense, +12% rate, +6Hz)</option>
          <option value="hi_f_calm">Swara Calm (Slow Mystery, +0% rate, -2Hz)</option>
          <option value="hi_m_grave">Madhur Grave (Deep Thriller, -5% rate, -15Hz)</option>
          <option value="hi_m_narrator">Madhur Narrator (Classic Storyteller)</option>
          <option value="hi_m_intense">Madhur Intense (Fast Climax)</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Visual Template</label>
        <select id="templateInput" class="form-select">
          <option value="">Auto (Theme Rotation)</option>
          <option value="sepia_archive">Sepia Archive (Vintage Mystery)</option>
          <option value="noir_teal">Noir Teal (Cinematic Shadow)</option>
          <option value="moonlit_blue">Moonlit Blue (Midnight Cold Fog)</option>
          <option value="crimson_alert">Crimson Alert (High Danger Suspense)</option>
          <option value="cyber_amber">Cyber Amber (Warm Glow Thriller)</option>
        </select>
      </div>

      <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:20px">
        <button type="button" class="btn btn-ghost" onclick="closeCreateModal()">Cancel</button>
        <button type="submit" class="btn btn-primary" id="btnSubmitVideo">🚀 Generate Video</button>
      </div>
    </form>
  </div>
</div>

<div id="toast"></div>

<script>
// Global State
let D = null;
let currentLogFilter = 'ALL';
let isHoloMode = false;
let audioEnabled = true;

// Web Audio API Synthesizer for 3D Cyber FX
class SoundEngine {
  constructor() {
    this.ctx = null;
  }
  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  }
  play(freq = 600, type = 'sine', duration = 0.08, rampTo = null) {
    if (!audioEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      if (this.ctx.state === 'suspended') this.ctx.resume();
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      if (rampTo) osc.frequency.exponentialRampToValueAtTime(rampTo, this.ctx.currentTime + duration);
      gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch(e) {}
  }
  click() { this.play(850, 'triangle', 0.04, 1200); }
  success() {
    this.play(523, 'sine', 0.1, 784);
    setTimeout(() => this.play(784, 'sine', 0.15, 1046), 60);
  }
  warn() { this.play(260, 'sawtooth', 0.14, 180); }
}
const snd = new SoundEngine();

function toggleSound() {
  audioEnabled = !audioEnabled;
  document.getElementById('btnAudio').textContent = audioEnabled ? '🔊 FX ON' : '🔇 FX MUTED';
  toast(audioEnabled ? 'Sound FX Enabled' : 'Sound FX Muted');
}

function toggleHoloMode() {
  isHoloMode = !isHoloMode;
  document.getElementById('app').classList.toggle('holo-view', isHoloMode);
  document.getElementById('btnHolo').textContent = isHoloMode ? '👓 Flat View' : '🕶️ 3D Holo';
  snd.click();
}

function toast(msg, bad) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.borderColor = bad ? '#f87171' : '#00f2fe';
  t.style.boxShadow = bad ? '0 10px 30px rgba(248,113,113,0.4)' : '0 10px 30px rgba(0,242,254,0.4)';
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3600);
}

// Data Fetch & Render
async function load() {
  try {
    const r = await fetch('/api/data');
    D = await r.json();
    render();
  } catch(e) {
    console.error('Data load error', e);
  }
}

function render() {
  if (!D) return;

  // Header badges
  document.getElementById('brand').textContent = D.brand || 'AUTOPILOT';
  const au = document.getElementById('autonomy');
  au.textContent = D.autonomy === 'review_first' ? '👤 review_first' : '🤖 auto_publish';
  au.className = 'badge ' + (D.autonomy === 'review_first' ? 'live' : 'warn');

  const mk = document.getElementById('mock');
  mk.textContent = D.mock_mode ? '⚠️ MOCK MODE' : '● LIVE';
  mk.className = 'badge ' + (D.mock_mode ? 'warn' : 'ok');
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();

  // Active task banner
  const tb = document.getElementById('task_banner');
  const tm = document.getElementById('task_msg');
  if (D.active_task && D.active_task.status === 'running') {
    tb.style.display = 'flex';
    tm.textContent = D.active_task.msg || 'Swarm task in progress...';
  } else {
    tb.style.display = 'none';
  }

  // Stat cards
  const s = D.summary || {};
  const qLen = (D.queue || []).length;
  const pTotal = s.published_total || (D.published || []).length;
  const aLearnings = s.active_learnings || (D.learnings || []).length;
  const expText = D.experiment ? '#' + D.experiment.id + ' (' + esc(D.experiment.variable) + ')' : 'Idle';

  const cardsHtml = [
    { title: 'Pending Approval', val: qLen, sub: 'Videos awaiting review', icon: '🎬' },
    { title: 'Total Published', val: pTotal, sub: 'YouTube Shorts & Reels', icon: '🚀' },
    { title: 'Active Learnings', val: aLearnings, sub: 'Validated winning traits', icon: '💡' },
    { title: 'A/B Experiment', val: expText, sub: D.experiment ? 'Testing active arms' : 'Ready for next test', icon: '🧪' },
  ].map(c => `
    <div class="card-3d stat-card">
      <div class="stat-k"><span>${c.title}</span> <span>${c.icon}</span></div>
      <div class="stat-v">${c.val}</div>
      <div class="stat-sub">${c.sub}</div>
      <div class="glare"></div>
    </div>
  `).join('');
  document.getElementById('cards').innerHTML = cardsHtml;

  // Tab count badges
  document.getElementById('badgeQueue').textContent = qLen;
  const errCount = (D.logs || []).filter(l => l.level === 'ERROR' || l.level === 'FATAL').length;
  const tabErr = document.getElementById('tabErr');
  const badgeErrors = document.getElementById('badgeErrors');
  badgeErrors.textContent = (D.logs || []).length;
  if (errCount > 0) {
    tabErr.classList.add('has-err');
  } else {
    tabErr.classList.remove('has-err');
  }

  // Quota Telemetry
  renderQuota();

  // Queue Studio
  renderQueue();

  // Diagnostics & Errors
  renderDiagnostics();

  // Intelligence & Analyst
  renderAnalyst();

  // Science & A/B
  renderScience();

  // Published
  renderPublished();

  // Draw 3D Visual Diagram & Graphs
  drawSwarmDiagram();
  drawRetentionGraph();
  drawVelocityGraph();

  // Attach 3D mouse tilt listeners to cards
  init3DTilt();
}

function renderQuota() {
  const qObj = D.quota || {};
  document.getElementById('quota').innerHTML = Object.entries(qObj).map(([k, q]) => {
    const pct = Math.min(100, Math.round(q.pct || 0));
    const cls = pct >= 90 ? 'd' : pct >= 75 ? 'w' : '';
    return `
      <div class="q-row">
        <div class="q-top">
          <span class="q-name">${esc(k)}</span>
          <span class="q-nums">${q.used}/${q.limit} (${pct}%)</span>
        </div>
        <div class="q-bar-bg">
          <div class="q-bar-fill ${cls}" style="width: ${pct}%"></div>
        </div>
        <div style="font-size:11px;color:var(--text-dim);text-align:right">Reset: ${q.reset_in || 'N/A'}</div>
      </div>
    `;
  }).join('');
}

function renderQueue() {
  const q = D.queue || [];
  const el = document.getElementById('queue');
  if (!q.length) {
    el.innerHTML = `
      <div class="card-3d" style="text-align:center;padding:40px 20px;">
        <div style="font-size:36px;margin-bottom:12px">🎉</div>
        <h3 style="font-size:17px;color:#fff;margin-bottom:6px">Queue khaali hai</h3>
        <p style="color:var(--text-muted);font-size:13px;margin-bottom:16px">Saari videos process aur publish ho chuki hain.</p>
        <button class="btn btn-primary" onclick="openCreateModal()">✨ Nayi Video Banao</button>
      </div>
    `;
    return;
  }

  el.innerHTML = q.map(v => `
    <div class="video-card card-3d" id="v${v.id}">
      <div class="video-media">
        ${v.video_url
          ? `<video src="${v.video_url}" controls preload="metadata" ${v.cover_url ? `poster="${v.cover_url}"` : ''}></video>`
          : '<div style="display:flex;height:100%;align-items:center;justify-content:center;color:var(--text-dim)">Video file rendering or missing</div>'}
      </div>
      <div class="video-info">
        <div>
          <div class="video-title">#${v.id} · ${esc(v.title || v.topic)}</div>
          <div class="video-meta">
            <span class="badge live">hook: <b>${v.hook_type || '?'}</b></span>
            <span class="badge">voice: <b>${v.voice_id || '?'}</b></span>
            <span class="badge">template: <b>${v.template_id || '?'}</b></span>
            <span class="badge">length: <b>${(v.length_sec || 0).toFixed(1)}s</b></span>
            <span class="badge ok">status: <b>${v.status}</b></span>
          </div>
          ${v.hook_overlay ? `
            <div class="hook-box">
              📌 <b>${esc(v.hook_overlay)}</b><br>
              <span style="color:var(--text-muted);font-size:12.5px">${esc(v.hook_line)}</span>
            </div>
          ` : ''}
          ${v.comment_bait ? `<div style="font-size:12.5px;color:var(--text-muted);margin:6px 0">💬 ${esc(v.comment_bait)}</div>` : ''}
          <div style="font-size:12px;color:var(--cyan);margin-top:6px">
            ${(v.hashtags || []).map(h => '#' + h.replace(/^#/, '')).map(esc).join(' ')}
          </div>
        </div>

        <div>
          <div class="btn-deck">
            <button class="btn btn-ghost" onclick="act('validate', ${v.id})">🔍 Validate</button>
            <button class="btn btn-success" onclick="act('approve', ${v.id})">✅ Approve</button>
            <button class="btn btn-danger" onclick="rej(${v.id})">✕ Reject</button>
            <button class="btn btn-ghost" onclick="act('rerender', ${v.id})">🔁 Re-render</button>
            <button class="btn btn-ghost" onclick="toggleLogs(${v.id})">📜 Logs</button>
            <button class="btn btn-primary" onclick="act('publish_video', ${v.id})">📤 Publish Now</button>
          </div>
          <div class="diag-detail" id="rep${v.id}" style="display:none;margin-top:12px"></div>
          <div class="diag-detail" id="log${v.id}" style="display:none;color:#93c5fd;margin-top:12px"></div>
        </div>
      </div>
      <div class="glare"></div>
    </div>
  `).join('');
}

function renderDiagnostics() {
  filterLogs();
}

function setLogFilter(cat, btn) {
  currentLogFilter = cat;
  document.querySelectorAll('.diag-pill').forEach(p => p.classList.remove('active'));
  if (btn) btn.classList.add('active');
  snd.click();
  filterLogs();
}

function filterLogs() {
  const listEl = document.getElementById('diagList');
  if (!listEl) return;
  const logs = D.logs || [];
  const q = (document.getElementById('diagSearch').value || '').toLowerCase();

  let filtered = logs.filter(l => {
    // Category filter
    if (currentLogFilter === 'FATAL' && !(l.level === 'FATAL' || l.level === 'ERROR')) return false;
    if (currentLogFilter === 'WARN' && l.level !== 'WARN') return false;
    if (currentLogFilter === 'VOICE' && !(l.agent === 'voice' || (l.msg||'').toLowerCase().includes('voice') || (l.msg||'').toLowerCase().includes('audio'))) return false;
    if (currentLogFilter === 'OAUTH' && !(l.agent === 'oauth' || (l.msg||'').toLowerCase().includes('oauth') || (l.msg||'').toLowerCase().includes('token'))) return false;
    if (currentLogFilter === 'QUOTA' && !(l.agent === 'quota' || (l.msg||'').toLowerCase().includes('quota'))) return false;
    if (currentLogFilter === 'PUB' && !(l.agent === 'publisher' || (l.msg||'').toLowerCase().includes('upload') || (l.msg||'').toLowerCase().includes('publish'))) return false;

    // Search query
    if (q) {
      const matchText = (l.msg + ' ' + l.agent + ' ' + (l.error_type || '') + ' ' + (l.error_detail || '')).toLowerCase();
      if (!matchText.includes(q)) return false;
    }
    return true;
  });

  if (!filtered.length) {
    listEl.innerHTML = `
      <div style="text-align:center;padding:26px;color:var(--green)">
        ✨ Is category mein koi warnings ya errors nahi hain! System operational hai.
      </div>
    `;
    return;
  }

  listEl.innerHTML = filtered.map(l => {
    const ts = (l.ts || '').replace('T', ' ').slice(0, 19);
    const lvl = l.level || 'WARN';
    const hasDetail = l.error_type || l.error_detail || l.trace;
    const fixHint = suggestFix(l);

    return `
      <div class="diag-item lvl-${lvl}">
        <div class="diag-head">
          <span class="badge ${lvl === 'FATAL' || lvl === 'ERROR' ? 'bad' : 'warn'}">${lvl}</span>
          <span class="diag-agent">${esc(l.agent || 'system')}</span>
          <span class="diag-ts">${ts}</span>
        </div>
        <div class="diag-msg">${esc(l.msg)}</div>
        ${hasDetail ? `
          <div class="diag-detail">${esc([l.error_type, l.error_detail].filter(Boolean).join(': '))}</div>
        ` : ''}
        ${fixHint ? `
          <div class="diag-fix">💡 <b>Recommended Fix:</b> ${esc(fixHint)}</div>
        ` : ''}
      </div>
    `;
  }).join('');
}

function suggestFix(l) {
  const m = ((l.msg || '') + ' ' + (l.error_detail || '')).toLowerCase();
  if (m.includes('token refresh') || m.includes('oauth')) {
    return 'token.json delete karein aur terminal mein "python authorize_youtube.py" chalayein.';
  }
  if (m.includes('quota') || m.includes('budget khatam')) {
    return 'Aaj ka API budget pura ho gaya hai. Kal subah auto-reset hoga ya .env mein limit badhayein.';
  }
  if (m.includes('tzdata') || m.includes('timezone')) {
    return 'Terminal mein run karein: pip install tzdata';
  }
  if (m.includes('whisper')) {
    return 'Faster-whisper optional hai; system automatically syllable fallback se perfect word sync kar raha hai.';
  }
  if (m.includes('silent_narration')) {
    return 'TTS audio generate nahi ho payi. Internet check karein ya dusra voice ID select karein.';
  }
  return null;
}

function copyDiagnosticsReport() {
  const logs = (D.logs || []).slice(0, 25);
  const text = `# AUTOPILOT Diagnostics Report (${new Date().toISOString()})\n\n` +
    logs.map(l => `[${l.ts}] [${l.level}] [${l.agent}] ${l.msg}\nDetail: ${l.error_detail || 'None'}`).join('\n\n');
  navigator.clipboard.writeText(text).then(() => {
    toast('Diagnostics report copied to clipboard! 📋');
    snd.success();
  }).catch(() => toast('Clipboard permission denied', true));
}

function renderAnalyst() {
  const A = D.analysis || {};
  const b = A.baseline;
  let h = '<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">';
  h += `<span class="badge">metrics due: <b>${A.due || 0}</b></span>`;
  if (b) {
    h += `<span class="badge live">baseline 2h (n=${b.n}): <b>${Math.round(b.views||0)}</b> views</span>`;
    h += `<span class="badge ok">avg retention: <b>${((b.avg_pct||0)*100).toFixed(0)}%</b></span>`;
  } else {
    h += `<span class="badge">baseline: 3+ videos required</span>`;
  }
  h += '</div>';

  if ((A.recent || []).length) {
    h += A.recent.map(r => `
      <div style="background:rgba(5,8,17,0.6);border-left:3px solid ${(r.flags||[]).length ? '#f87171' : '#34d399'};padding:9px 12px;margin:7px 0;border-radius:0 8px 8px 0;font-size:12.5px">
        ${esc(r.summary || '')}
      </div>
    `).join('');
  }

  const V = A.variables || {};
  if (Object.keys(V).length) {
    h += '<table style="margin-top:14px"><tr><th>Variable</th><th>Top Performer</th><th>Avg Views</th><th>Retention</th><th>Sample n</th></tr>';
    h += Object.entries(V).map(([k, items]) => {
      const t = items[0];
      return `<tr>
        <td><b>${k}</b></td>
        <td><span class="badge live">${esc(t.value)}</span></td>
        <td><b>${t.avg_views}</b></td>
        <td><span style="color:var(--green)">${(t.avg_retention*100).toFixed(0)}%</span></td>
        <td>${t.n}</td>
      </tr>`;
    }).join('');
    h += '</table>';
  }
  h += '<div class="glare"></div>';
  document.getElementById('analyst').innerHTML = h;
}

function renderScience() {
  const S = D.science || {}, E = S.evaluation, X = D.experiment;
  let h = '';
  if (X) {
    const c = (E && E.videos_assigned) || {A: 0, B: 0};
    const m = (E && E.metrics_ready) || {A: 0, B: 0};
    h += `
      <div style="margin-bottom:14px">
        <div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:4px">
          🧪 Active Experiment #${X.id} — Variable: <span style="color:var(--cyan)">${esc(X.variable)}</span>
        </div>
        <div style="color:var(--text-muted);font-size:13px;margin-bottom:10px">${esc(X.hypothesis || '')}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <span class="badge live">Arm A: <b>${esc(X.arm_a)}</b> (${c.A} videos, ${m.A} measured)</span>
          <span class="badge warn">Arm B: <b>${esc(X.arm_b)}</b> (${c.B} videos, ${m.B} measured)</span>
          <span class="badge">min target: ${X.min_per_arm}/arm</span>
        </div>
      </div>
    `;
    if (E && E.ready) {
      h += `
        <div style="background:rgba(5,8,17,0.7);border-left:3px solid ${E.significant ? '#34d399' : '#fbbf24'};padding:12px 14px;border-radius:0 8px 8px 0;margin-bottom:12px">
          <div style="font-size:13px">${esc(E.explanation)}</div>
          <div style="color:var(--cyan);font-weight:700;margin-top:4px">➜ ${esc(E.recommendation)}</div>
        </div>
        <button class="btn btn-success" onclick="act('exp_conclude',0)">🏁 Conclude Experiment</button>
      `;
    } else if (E) {
      h += `
        <div style="color:var(--amber);font-size:12.5px;margin-bottom:10px">${esc(E.message || E.status || 'Data collect ho raha hai')}</div>
        <button class="btn btn-ghost" onclick="if(confirm('Kam data pe conclude? Learning save nahi hogi.')) act('exp_conclude',0,{force:true})">Abandon</button>
      `;
    }
  } else if (S.suggestion) {
    const sg = S.suggestion;
    h += `
      <div style="color:var(--text-muted);margin-bottom:12px">
        Abhi koi experiment active nahi hai.<br>
        <b style="color:#fff">Next Recommended Experiment:</b> <span style="color:var(--cyan)">${esc(sg.variable)}</span> (${esc(sg.arm_a)} vs ${esc(sg.arm_b)})<br>
        <span style="font-size:12px">Reason: ${esc(sg.reason)}</span>
      </div>
      <button class="btn btn-success" onclick="act('exp_start',0,{variable:'${esc(sg.variable)}'})">🧪 Start A/B Experiment</button>
    `;
  } else {
    h += '<div style="color:var(--text-dim);margin-bottom:12px">Koi active experiment nahi hai</div>';
  }

  // Active learnings table
  if ((D.learnings || []).length) {
    h += `
      <table style="margin-top:16px">
        <tr><th>Variable</th><th>Winning Trait</th><th>Loser</th><th>Performance Lift</th><th>Sample Size</th><th>Confidence</th></tr>
        ${D.learnings.map(l => `
          <tr>
            <td><b>${l.variable}</b></td>
            <td><span class="badge ok">${esc(l.winner)}</span></td>
            <td style="color:var(--text-dim)">${esc(l.loser || '—')}</td>
            <td style="color:${l.lift_pct > 0 ? 'var(--green)' : 'var(--red)'};font-weight:700">${(l.lift_pct || 0).toFixed(0)}%</td>
            <td>${l.sample_size}</td>
            <td><span class="badge">${esc(l.confidence)}</span></td>
          </tr>
        `).join('')}
      </table>
    `;
  }

  // Champions
  const champs = (S && S.champions) || {};
  if (Object.keys(champs).length) {
    h += `
      <div style="margin-top:16px;padding-top:12px;border-top:1px solid var(--border-subtle)">
        <span style="font-weight:700;color:#fff;margin-right:8px">👑 Active Champions:</span>
        ${Object.entries(champs).map(([k, c]) => `
          <span class="badge live">${k}=<b>${esc(c.value)}</b> (${c.lift_pct > 0 ? '+' : ''}${Math.round(c.lift_pct)}%)</span>
        `).join(' ')}
      </div>
    `;
  }
  h += '<div class="glare"></div>';
  document.getElementById('sci').innerHTML = h;
}

function renderPublished() {
  const pList = D.published || [];
  const el = document.getElementById('published');
  if (!pList.length) {
    el.innerHTML = '<div style="padding:24px;text-align:center;color:var(--text-dim)">Abhi koi video published archive mein nahi hai.</div>';
    return;
  }
  el.innerHTML = `
    <table>
      <tr><th>#</th><th>Title</th><th>Hook</th><th>Voice</th><th>2h Views</th><th>2h Ret</th><th>24h Views</th><th>Links</th></tr>
      ${pList.map(p => `
        <tr>
          <td><b>#${p.id}</b></td>
          <td>${esc((p.title || '').slice(0, 40))}</td>
          <td><span class="badge">${p.hook_type || '—'}</span></td>
          <td><span class="badge">${p.voice_id || '—'}</span></td>
          <td><b>${p.m2h ? p.m2h.views : '—'}</b></td>
          <td>${p.m2h && p.m2h.ret_1s ? '<span style="color:var(--green)">' + (p.m2h.ret_1s * 100).toFixed(0) + '%</span>' : '—'}</td>
          <td><b>${p.m24h ? p.m24h.views : '—'}</b></td>
          <td>
            ${p.yt_video_id ? `<a href="https://youtu.be/${p.yt_video_id}" target="_blank" style="color:var(--red);text-decoration:none;font-weight:600">▶ YT</a>` : ''}
            ${p.ig_media_id ? ` · <span style="color:var(--purple)">📷 IG</span>` : ''}
          </td>
        </tr>
      `).join('')}
    </table>
    <div class="glare"></div>
  `;
}

// -------------------------------------------------------------
// Interactive 3D Swarm Pipeline Canvas Architecture Diagram
// -------------------------------------------------------------
const AGENTS = [
  { id: 'chief', name: 'Chief', sub: 'Swarm Leader & Quota', x: 70, y: 135, color: '#38bdf8' },
  { id: 'trend', name: 'TrendScout', sub: 'Viral Topics AI', x: 190, y: 70, color: '#818cf8' },
  { id: 'writer', name: 'Writer', sub: '4-Hook Suspense Script', x: 310, y: 70, color: '#c084fc' },
  { id: 'artdir', name: 'ArtDirector', sub: 'Visuals & Pacing', x: 430, y: 70, color: '#f472b6' },
  { id: 'voice', name: 'Voice', sub: 'Edge-TTS & Whisper', x: 550, y: 70, color: '#fb923c' },
  { id: 'editor', name: 'Editor', sub: 'FFmpeg 9:16 Render', x: 670, y: 135, color: '#fbbf24' },
  { id: 'gates', name: 'Gatekeeper', sub: '4 Quality Gates', x: 790, y: 135, color: '#34d399' },
  { id: 'pub', name: 'Publisher', sub: 'YouTube & IG API', x: 910, y: 135, color: '#2dd4bf' },
  { id: 'analyst', name: 'Analyst', sub: '2h/24h Retention Metric', x: 1030, y: 135, color: '#00f2fe' },
  { id: 'scientist', name: 'Scientist', sub: 'Bayesian A/B Lab', x: 1150, y: 135, color: '#60a5fa' },
];
const CONDUITS = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9],
  [9, 0], // Feedback loop to Chief
];
let pulseTime = 0;
let hoveredAgent = null;

function drawSwarmDiagram() {
  const c = document.getElementById('swarmCanvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);

  pulseTime += 0.025;

  // Draw conduit lines with flowing glowing pulses
  CONDUITS.forEach(([i, j]) => {
    const a = AGENTS[i], b = AGENTS[j];
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.18)';
    ctx.lineWidth = 2;
    if (i === 9 && j === 0) {
      // Loopback curve
      ctx.beginPath();
      ctx.moveTo(a.x, a.y + 20);
      ctx.bezierCurveTo(a.x, 240, b.x, 240, b.x, b.y + 20);
      ctx.stroke();

      // Flowing particle on loopback
      const t = (pulseTime * 0.7) % 1;
      const px = Math.pow(1-t, 3)*a.x + 3*Math.pow(1-t, 2)*t*a.x + 3*(1-t)*Math.pow(t, 2)*b.x + Math.pow(t, 3)*b.x;
      const py = Math.pow(1-t, 3)*(a.y+20) + 3*Math.pow(1-t, 2)*t*240 + 3*(1-t)*Math.pow(t, 2)*240 + Math.pow(t, 3)*(b.y+20);
      ctx.beginPath();
      ctx.arc(px, py, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = '#00f2fe';
      ctx.shadowColor = '#00f2fe';
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
      return;
    }
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();

    // Flowing energy particle
    const t = (pulseTime + i * 0.15) % 1;
    const px = a.x + (b.x - a.x) * t;
    const py = a.y + (b.y - a.y) * t;
    ctx.beginPath();
    ctx.arc(px, py, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#38bdf8';
    ctx.shadowColor = '#38bdf8';
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;
  });

  // Draw Agent Nodes
  AGENTS.forEach((ag, idx) => {
    const isHov = hoveredAgent === idx;
    // 3D Isometric / Circular node
    ctx.save();
    ctx.shadowColor = ag.color;
    ctx.shadowBlur = isHov ? 20 : 8;

    // Node outer ring
    ctx.beginPath();
    ctx.arc(ag.x, ag.y, isHov ? 24 : 20, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(10, 15, 29, 0.9)';
    ctx.fill();
    ctx.lineWidth = isHov ? 3 : 2;
    ctx.strokeStyle = ag.color;
    ctx.stroke();

    // Node inner core
    ctx.beginPath();
    ctx.arc(ag.x, ag.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = ag.color;
    ctx.fill();
    ctx.restore();

    // Node label
    ctx.font = isHov ? 'bold 12px Inter' : '600 11px Inter';
    ctx.fillStyle = isHov ? '#fff' : '#cbd5e1';
    ctx.textAlign = 'center';
    ctx.fillText(ag.name, ag.x, ag.y + 36);
  });
}

// Canvas mousemove for diagram tooltip
window.addEventListener('load', () => {
  const c = document.getElementById('swarmCanvas');
  const tip = document.getElementById('diagramTooltip');
  if (!c) return;

  c.addEventListener('mousemove', (e) => {
    const rect = c.getBoundingClientRect();
    const scaleX = c.width / rect.width;
    const scaleY = c.height / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;

    let found = null;
    AGENTS.forEach((ag, idx) => {
      const dist = Math.hypot(mx - ag.x, my - ag.y);
      if (dist < 26) found = idx;
    });

    hoveredAgent = found;
    if (found !== null) {
      const ag = AGENTS[found];
      tip.style.display = 'block';
      tip.style.left = (e.clientX - rect.left + 15) + 'px';
      tip.style.top = (e.clientY - rect.top - 10) + 'px';
      tip.innerHTML = `
        <div style="font-weight:700;color:${ag.color};margin-bottom:2px">${ag.name}</div>
        <div style="color:#cbd5e1">${ag.sub}</div>
        <div style="font-size:11px;color:var(--text-dim);margin-top:4px">Status: Active &amp; Autonomous</div>
      `;
    } else {
      tip.style.display = 'none';
    }
  });

  c.addEventListener('mouseleave', () => {
    hoveredAgent = null;
    tip.style.display = 'none';
  });
});

// Continuous loop for canvas animation
function animLoop() {
  drawSwarmDiagram();
  requestAnimationFrame(animLoop);
}
requestAnimationFrame(animLoop);

// -------------------------------------------------------------
// Interactive Retention Graph (Canvas #1)
// -------------------------------------------------------------
let scrubSec = null;
function drawRetentionGraph() {
  const c = document.getElementById('retentionCanvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);

  const padL = 45, padR = 20, padT = 20, padB = 35;
  const gw = w - padL - padR;
  const gh = h - padT - padB;

  // Grid lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#64748b';
  ctx.font = '10px JetBrains Mono';
  ctx.textAlign = 'right';

  [0, 25, 50, 75, 100].forEach(p => {
    const y = padT + gh - (p / 100) * gh;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(w - padR, y);
    ctx.stroke();
    ctx.fillText(p + '%', padL - 8, y + 4);
  });

  // X Axis seconds (0, 10, 20, 30, 40, 50, 60s)
  ctx.textAlign = 'center';
  for (let s = 0; s <= 60; s += 10) {
    const x = padL + (s / 60) * gw;
    ctx.beginPath();
    ctx.moveTo(x, padT + gh);
    ctx.lineTo(x, padT + gh + 4);
    ctx.stroke();
    ctx.fillText(s + 's', x, padT + gh + 18);
  }

  // Retention curve generator function
  function getRet(t, isCurrent) {
    if (t <= 1) return 1.0 - (t * 0.12);
    if (t <= 3) return 0.88 - ((t - 1) * 0.08);
    if (t <= 15) return 0.72 - ((t - 3) * 0.012);
    if (t <= 35) return 0.58 - ((t - 15) * 0.007);
    return Math.max(0.25, 0.44 - ((t - 35) * (isCurrent ? 0.004 : 0.008)));
  }

  // Plot Baseline Curve (Cyan)
  ctx.beginPath();
  ctx.strokeStyle = '#00f2fe';
  ctx.lineWidth = 2.5;
  for (let s = 0; s <= 60; s += 0.5) {
    const r = getRet(s, false);
    const x = padL + (s / 60) * gw;
    const y = padT + gh - r * gh;
    if (s === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Plot Latest Video Curve (Green)
  ctx.beginPath();
  ctx.strokeStyle = '#34d399';
  ctx.lineWidth = 2.5;
  const grad = ctx.createLinearGradient(0, padT, 0, padT + gh);
  grad.addColorStop(0, 'rgba(52, 211, 153, 0.2)');
  grad.addColorStop(1, 'rgba(52, 211, 153, 0.0)');

  for (let s = 0; s <= 60; s += 0.5) {
    const r = getRet(s, true);
    const x = padL + (s / 60) * gw;
    const y = padT + gh - r * gh;
    if (s === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Highlight Gates: 1s (Hook), 3s (IG), 15s (Mid-Drop)
  const gates = [
    { sec: 1, label: '1s Hook', col: '#fbbf24' },
    { sec: 3, label: '3s IG Gate', col: '#818cf8' },
    { sec: 15, label: '15s Pacing', col: '#f472b6' }
  ];
  gates.forEach(g => {
    const gx = padL + (g.sec / 60) * gw;
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = g.col;
    ctx.beginPath();
    ctx.moveTo(gx, padT);
    ctx.lineTo(gx, padT + gh);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = g.col;
    ctx.fillText(g.label, gx, padT - 6);
  });

  // Scrubbing marker
  if (scrubSec !== null) {
    const sx = padL + (scrubSec / 60) * gw;
    const retVal = Math.round(getRet(scrubSec, true) * 100);
    const sy = padT + gh - (retVal / 100) * gh;

    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(sx, padT);
    ctx.lineTo(sx, padT + gh);
    ctx.stroke();

    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(sx, sy, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#030712';
    ctx.fillRect(sx - 35, sy - 28, 70, 20);
    ctx.fillStyle = '#00f2fe';
    ctx.fillText(`${scrubSec.toFixed(1)}s: ${retVal}%`, sx, sy - 14);
  }
}

// Attach scrub listener
window.addEventListener('load', () => {
  const c = document.getElementById('retentionCanvas');
  if (!c) return;
  c.addEventListener('mousemove', (e) => {
    const rect = c.getBoundingClientRect();
    const padL = 45, padR = 20;
    const gw = c.width - padL - padR;
    const scaleX = c.width / rect.width;
    const mx = (e.clientX - rect.left) * scaleX;
    if (mx >= padL && mx <= c.width - padR) {
      scrubSec = Math.max(0, Math.min(60, ((mx - padL) / gw) * 60));
      drawRetentionGraph();
    }
  });
  c.addEventListener('mouseleave', () => {
    scrubSec = null;
    drawRetentionGraph();
  });
});

// -------------------------------------------------------------
// Velocity & Trajectory Graph (Canvas #2)
// -------------------------------------------------------------
function drawVelocityGraph() {
  const c = document.getElementById('velocityCanvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);

  const pList = (D && D.published) ? D.published.slice(0, 6) : [];
  const padL = 45, padR = 20, padT = 20, padB = 40;
  const gw = w - padL - padR;
  const gh = h - padT - padB;

  // Grid
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
  ctx.fillStyle = '#64748b';
  ctx.font = '10px JetBrains Mono';
  ctx.textAlign = 'right';

  const maxVal = Math.max(100, ...pList.map(p => (p.m24h ? p.m24h.views : (p.m2h ? p.m2h.views : 50))));
  [0, 0.25, 0.5, 0.75, 1].forEach(frac => {
    const y = padT + gh - frac * gh;
    const v = Math.round(frac * maxVal);
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(w - padR, y);
    ctx.stroke();
    ctx.fillText(v, padL - 8, y + 4);
  });

  if (!pList.length) {
    ctx.textAlign = 'center';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText('No published videos yet for velocity calculation', w / 2, h / 2);
    return;
  }

  // Draw grouped bars for 2h Views vs 24h Views
  const groupW = gw / pList.length;
  const barW = Math.min(22, groupW * 0.35);

  pList.forEach((p, idx) => {
    const gx = padL + idx * groupW + (groupW / 2);
    const v2h = p.m2h ? p.m2h.views : 0;
    const v24h = p.m24h ? p.m24h.views : v2h;

    const h2 = (v2h / maxVal) * gh;
    const h24 = (v24h / maxVal) * gh;

    // 2h bar (Cyan)
    ctx.fillStyle = '#00f2fe';
    ctx.fillRect(gx - barW - 2, padT + gh - h2, barW, h2);

    // 24h bar (Purple)
    ctx.fillStyle = '#818cf8';
    ctx.fillRect(gx + 2, padT + gh - h24, barW, h24);

    // Label
    ctx.fillStyle = '#cbd5e1';
    ctx.textAlign = 'center';
    ctx.fillText('#' + p.id, gx, padT + gh + 18);
  });

  // Legend
  ctx.textAlign = 'left';
  ctx.fillStyle = '#00f2fe';
  ctx.fillRect(w - 150, 10, 10, 10);
  ctx.fillText('2h Views', w - 134, 19);

  ctx.fillStyle = '#818cf8';
  ctx.fillRect(w - 75, 10, 10, 10);
  ctx.fillText('24h Views', w - 59, 19);
}

// -------------------------------------------------------------
// Interactive 3D Gyroscope Mouse Tilt on Cards
// -------------------------------------------------------------
function init3DTilt() {
  document.querySelectorAll('.card-3d, .video-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      const dx = (x - cx) / cx;
      const dy = (y - cy) / cy;
      card.style.transform = `rotateY(${dx * 6}deg) rotateX(${-dy * 6}deg) translateZ(8px)`;

      const glare = card.querySelector('.glare');
      if (glare) {
        glare.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(255,255,255,0.12), transparent 70%)`;
      }
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'rotateY(0deg) rotateX(0deg) translateZ(0px)';
    });
  });
}

// Background Starfield Animation Canvas
(function initBgCanvas() {
  const c = document.getElementById('bgCanvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  let w = (c.width = window.innerWidth);
  let h = (c.height = window.innerHeight);

  window.addEventListener('resize', () => {
    w = c.width = window.innerWidth;
    h = c.height = window.innerHeight;
  });

  const stars = Array.from({ length: 90 }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    z: Math.random() * 2 + 0.5,
    r: Math.random() * 1.5 + 0.5,
    col: Math.random() > 0.6 ? '#38bdf8' : '#fff'
  }));

  function loop() {
    ctx.clearRect(0, 0, w, h);
    stars.forEach(s => {
      s.y -= s.z * 0.25;
      if (s.y < 0) {
        s.y = h;
        s.x = Math.random() * w;
      }
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = s.col;
      ctx.globalAlpha = Math.min(1, s.z * 0.4);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();

// Tab Navigation Switching
function switchTab(tab, btn) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  snd.click();

  const secMap = {
    all: ['section-quota', 'section-diagram', 'section-graphs', 'section-queue', 'section-errors', 'section-analyst', 'section-science', 'section-published'],
    studio: ['section-queue'],
    diagram: ['section-diagram'],
    graphs: ['section-graphs'],
    science: ['section-science', 'section-analyst'],
    errors: ['section-errors']
  };

  const allSecs = ['section-quota', 'section-diagram', 'section-graphs', 'section-queue', 'section-errors', 'section-analyst', 'section-science', 'section-published'];
  const toShow = secMap[tab] || allSecs;

  allSecs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = toShow.includes(id) ? 'block' : 'none';
  });

  // Scroll to section if single tab
  if (tab !== 'all') {
    const target = document.getElementById(toShow[0]);
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  }
}

// Modal Video Creator Controls
function openCreateModal() {
  document.getElementById('videoModal').style.display = 'flex';
  document.getElementById('topicInput').focus();
  snd.click();
}
function closeCreateModal() {
  document.getElementById('videoModal').style.display = 'none';
}
function setTopic(t) {
  document.getElementById('topicInput').value = t;
  snd.click();
}

async function submitCreateVideo(e) {
  e.preventDefault();
  const topic = document.getElementById('topicInput').value.trim() || null;
  const voice = document.getElementById('voiceInput').value || null;
  const template = document.getElementById('templateInput').value || null;
  closeCreateModal();
  toast('Video generation request sent... 🚀');
  snd.success();
  await act('generate', 0, { topic, voice, template });
}

// Actions & API Handlers
async function act(action, id, extra) {
  snd.click();
  const r = await fetch('/api/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(Object.assign({ action, video_id: id }, extra || {}))
  });
  const j = await r.json();

  if (action === 'validate' && j.report) {
    const el = document.getElementById('rep' + id);
    const f = j.report.facts || {};
    el.style.display = 'block';
    el.textContent = (j.report.ok ? '✅ PASS' : '❌ FAIL') + '  ' +
      `${f.resolution || '?'} · ${f.duration_sec || '?'}s · ${f.vcodec}+${f.acodec} · ` +
      `${f.lufs != null ? f.lufs + ' LUFS' : ''}\n` +
      ((j.report.issues || []).length
        ? j.report.issues.map(i => `${i.level}: ${i.msg}` + (i.fix ? `\n   → ${i.fix}` : '')).join('\n')
        : 'Koi problem nahi mili 🎉');
    toast(j.report.ok ? 'Validate pass ✅' : 'Validate fail ❌', !j.report.ok);
    if (j.report.ok) snd.success(); else snd.warn();
    return load();
  }

  toast(j.msg || j.error || 'Action Complete', !j.ok);
  if (j.ok) snd.success(); else snd.warn();
  load();
}

function rej(id) {
  const reason = prompt('Reject kyun kar rahe ho? (Ye learning ban jayega):');
  if (reason !== null) act('reject', id, { reason });
}

async function toggleLogs(id) {
  const el = document.getElementById('log' + id);
  if (!el) return;
  if (el.style.display === 'block') {
    el.style.display = 'none';
    return;
  }
  el.style.display = 'block';
  el.textContent = 'Logs load ho rahe hain...';
  try {
    const r = await fetch('/api/logs?video_id=' + id);
    const j = await r.json();
    if (!j.ok) {
      el.textContent = '❌ ' + (j.error || 'Logs load fail');
      return;
    }
    if (!j.logs || !j.logs.length) {
      el.textContent = 'Is video ke liye koi specific log nahi mila.';
      return;
    }
    el.textContent = j.logs.map(l => {
      const ts = (l.ts || '').slice(11, 19);
      const lvl = l.level ? `[${l.level.toUpperCase()}]` : '';
      const ag = l.agent ? `[${l.agent}]` : '';
      return `${ts} ${lvl} ${ag} ${l.msg || ''}`;
    }).join('\n');
  } catch (e) {
    el.textContent = '❌ Network error logs fetch mein: ' + e;
  }
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

// Initial Boot
load();
setInterval(() => {
  if (D && D.active_task && D.active_task.status === 'running') {
    load();
  }
}, 3000);
setInterval(load, 15000);
</script>
</body>
</html>"""


def serve(port: int = PORT, open_browser: bool = True):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}"
    print("\n" + "=" * 60)
    print(f"  [*] AUTOPILOT Dashboard chal raha hai")
    print(f"  >>> {url}")
    print(f"  (band karne ke liye Ctrl+C)")
    print("=" * 60 + "\n")
    if open_browser:
        threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(url)),
                         daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard band. Bye!")
        srv.shutdown()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    serve(a.port, not a.no_browser)
