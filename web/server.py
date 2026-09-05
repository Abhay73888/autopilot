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
<html lang="hi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AUTOPILOT Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#e6edf3;font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:20px 24px 60px}
h1{font-size:20px;letter-spacing:.5px}h2{font-size:15px;margin:26px 0 12px;color:#7d8590;text-transform:uppercase;letter-spacing:1.2px}
a{color:#58a6ff}
.top{display:flex;align-items:center;gap:14px;flex-wrap:wrap;border-bottom:1px solid #21262d;padding-bottom:14px}
.badge{font-size:11px;padding:3px 9px;border-radius:20px;background:#21262d;color:#7d8590;font-weight:600}
.badge.warn{background:#3d2b00;color:#e3b341}.badge.ok{background:#0f2f1a;color:#3fb950}.badge.bad{background:#3d1519;color:#f85149}
.grid{display:grid;gap:14px}
.cards{grid-template-columns:repeat(auto-fill,minmax(230px,1fr))}
.card{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px}
.card .k{font-size:11px;color:#7d8590;text-transform:uppercase;letter-spacing:.8px}
.card .v{font-size:26px;font-weight:700;margin-top:5px}
.q{display:flex;align-items:center;gap:10px;margin:7px 0;font-size:12px}
.q .name{width:140px;color:#7d8590;flex-shrink:0}
.bar{flex:1;height:7px;background:#21262d;border-radius:4px;overflow:hidden}
.bar i{display:block;height:100%;background:#3fb950;border-radius:4px}
.bar.w i{background:#e3b341}.bar.d i{background:#f85149}
.q .n{width:110px;text-align:right;color:#7d8590;font-variant-numeric:tabular-nums}
.vid{display:grid;grid-template-columns:220px 1fr;gap:18px;background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px;margin-bottom:14px}
.vid video{width:100%;border-radius:8px;background:#000;display:block}
.meta{display:flex;gap:7px;flex-wrap:wrap;margin:9px 0}
.chip{font-size:11px;padding:3px 9px;background:#21262d;border-radius:5px;color:#8b949e}
.chip b{color:#e6edf3;font-weight:600}
.hook{background:#0d1117;border-left:3px solid #e3b341;padding:9px 12px;border-radius:0 6px 6px 0;margin:9px 0;font-size:13px}
.btns{display:flex;gap:9px;margin-top:12px;flex-wrap:wrap}
button{border:0;border-radius:7px;padding:9px 18px;font-weight:600;font-size:13px;cursor:pointer;font-family:inherit}
.ok{background:#238636;color:#fff}.ok:hover{background:#2ea043}
.no{background:#21262d;color:#f85149}.no:hover{background:#30363d}
.gr{background:#21262d;color:#c9d1d9}.gr:hover{background:#30363d}
button:disabled{opacity:.45;cursor:not-allowed}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;color:#7d8590;font-weight:600;padding:7px 10px;border-bottom:1px solid #21262d;font-size:11px;text-transform:uppercase}
td{padding:8px 10px;border-bottom:1px solid #161b22}
.empty{color:#6e7681;padding:22px;text-align:center;background:#161b22;border:1px dashed #21262d;border-radius:10px}
.log{font:11.5px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;background:#161b22;border:1px solid #21262d;border-radius:10px;padding:12px;max-height:300px;overflow:auto}
.log div{padding:2px 0;border-bottom:1px solid #0d1117}
.lv-WARN{color:#e3b341}.lv-ERROR,.lv-FATAL{color:#f85149}
#toast{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;padding:13px 22px;border-radius:9px;display:none;font-weight:600;box-shadow:0 6px 24px rgba(0,0,0,.5);z-index:99}
.rep{font:11.5px/1.5 ui-monospace,monospace;background:#0d1117;border-radius:7px;padding:10px;margin-top:10px;white-space:pre-wrap;max-height:200px;overflow:auto}
.task-banner{background:#1f6feb;color:#fff;padding:12px 18px;border-radius:8px;margin:14px 0;font-weight:600;display:flex;align-items:center;gap:12px;box-shadow:0 4px 12px rgba(31,111,235,.3)}
.task-spinner{width:16px;height:16px;border:3px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style></head><body>

<div class="top">
  <h1>🎬 <span id="brand">AUTOPILOT</span></h1>
  <span class="badge" id="autonomy"></span>
  <span class="badge" id="mock"></span>
  <span style="flex:1"></span>
  <button class="ok" onclick="generateVideo()" title="Nayi video banao (Topic choose kar sakte hain)">✨ Nayi Video Banao</button>
  <button class="gr" onclick="act('tick',0)" title="Ek cycle chalao (metrics, experiment, publish, produce)">⚡ Run Swarm Tick</button>
  <span class="badge" id="clock"></span>
</div>

<div id="task_banner" class="task-banner" style="display:none">
  <div class="task-spinner"></div>
  <span id="task_msg">Task chal raha hai...</span>
</div>

<h2>Overview</h2>
<div class="grid cards" id="cards"></div>

<h2>✅ Approve Queue</h2>
<div id="queue"></div>

<h2>📊 Quota</h2>
<div class="card" id="quota"></div>

<h2>📈 Published</h2>
<div id="published"></div>

<h2>🔬 Analyst</h2>
<div class="card" id="analyst"></div>

<h2>🧪 Experiment &amp; Learnings</h2>
<div class="card" id="sci"></div>

<h2>⚠️ Aaj ke Warnings / Errors</h2>
<div class="log" id="logs"></div>

<div id="toast"></div>

<script>
let D = null;

function toast(msg, bad) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = bad ? '#da3633' : '#238636';
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3500);
}

async function load() {
  const r = await fetch('/api/data');
  D = await r.json();
  render();
}

function render() {
  document.getElementById('brand').textContent = D.brand;
  const au = document.getElementById('autonomy');
  au.textContent = D.autonomy === 'review_first' ? '👤 review_first' : '🤖 auto_publish';
  au.className = 'badge ' + (D.autonomy === 'review_first' ? '' : 'warn');
  const mk = document.getElementById('mock');
  mk.textContent = D.mock_mode ? '⚠️ MOCK MODE' : '● LIVE';
  mk.className = 'badge ' + (D.mock_mode ? 'warn' : 'ok');
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();

  // active task banner
  const tb = document.getElementById('task_banner');
  const tm = document.getElementById('task_msg');
  if (D.active_task && D.active_task.status === 'running') {
    tb.style.display = 'flex';
    tm.textContent = D.active_task.msg || 'Task chal raha hai...';
  } else {
    tb.style.display = 'none';
  }

  // cards
  const s = D.summary;
  const cards = [
    ['Pending approval', D.queue.length],
    ['Published', s.published_total || 0],
    ['Active learnings', s.active_learnings || 0],
    ['Experiment', D.experiment ? '#' + D.experiment.id : '—'],
  ];
  document.getElementById('cards').innerHTML = cards.map(
    c => `<div class="card"><div class="k">${c[0]}</div><div class="v">${c[1]}</div></div>`).join('');

  // queue
  document.getElementById('queue').innerHTML = D.queue.length ? D.queue.map(v => `
    <div class="vid" id="v${v.id}">
      <div>${v.video_url
        ? `<video src="${v.video_url}" controls preload="metadata"
             ${v.cover_url ? `poster="${v.cover_url}"` : ''}></video>`
        : '<div class="empty">video nahi</div>'}</div>
      <div>
        <div style="font-size:16px;font-weight:600">#${v.id} · ${esc(v.title || v.topic)}</div>
        <div class="meta">
          <span class="chip">hook <b>${v.hook_type || '?'}</b></span>
          <span class="chip">voice <b>${v.voice_id || '?'}</b></span>
          <span class="chip">template <b>${v.template_id || '?'}</b></span>
          <span class="chip">length <b>${(v.length_sec || 0).toFixed(1)}s</b></span>
          <span class="chip">status <b>${v.status}</b></span>
        </div>
        ${v.hook_overlay ? `<div class="hook">📌 <b>${esc(v.hook_overlay)}</b><br>
          <span style="color:#8b949e">${esc(v.hook_line)}</span></div>` : ''}
        ${v.comment_bait ? `<div style="font-size:12.5px;color:#8b949e">
          💬 ${esc(v.comment_bait)}</div>` : ''}
        <div style="font-size:12px;color:#58a6ff;margin-top:7px">
          ${(v.hashtags || []).map(esc).join(' ')}</div>
        <div class="btns">
          <button class="gr" onclick="act('validate',${v.id})">🔍 Validate</button>
          <button class="ok" onclick="act('approve',${v.id})">✅ Approve</button>
          <button class="no" onclick="rej(${v.id})">✕ Reject</button>
          <button class="gr" onclick="act('rerender',${v.id})">🔁 Re-render</button>
          <button class="gr" onclick="toggleLogs(${v.id})">📜 Logs</button>
          <button class="ok" style="background:#1f6feb" onclick="act('publish_video',${v.id})">📤 Publish Now</button>
        </div>
        <div class="rep" id="rep${v.id}" style="display:none"></div>
        <div class="rep" id="log${v.id}" style="display:none;background:#030712;color:#a5d6ff"></div>
      </div>
    </div>`).join('') : '<div class="empty">Queue khaali hai — <b>"✨ Nayi Video Banao"</b> button dabayein</div>';

  // quota
  document.getElementById('quota').innerHTML = Object.entries(D.quota).map(([k, q]) => {
    const cls = q.pct >= 90 ? 'd' : q.pct >= 80 ? 'w' : '';
    return `<div class="q"><span class="name">${k}</span>
      <span class="bar ${cls}"><i style="width:${Math.min(100, q.pct)}%"></i></span>
      <span class="n">${q.used}/${q.limit} · ${q.reset_in}</span></div>`;
  }).join('');

  // published
  document.getElementById('published').innerHTML = D.published.length ? `<table>
    <tr><th>#</th><th>Title</th><th>Hook</th><th>Voice</th>
        <th>2h views</th><th>2h ret</th><th>24h views</th></tr>
    ${D.published.map(p => `<tr>
      <td>${p.id}</td><td>${esc((p.title || '').slice(0, 42))}</td>
      <td>${p.hook_type || '—'}</td><td>${p.voice_id || '—'}</td>
      <td><b>${p.m2h ? p.m2h.views : '—'}</b></td>
      <td>${p.m2h && p.m2h.ret_1s ? (p.m2h.ret_1s * 100).toFixed(0) + '%' : '—'}</td>
      <td>${p.m24h ? p.m24h.views : '—'}</td></tr>`).join('')}</table>`
    : '<div class="empty">Abhi kuch publish nahi hua (Phase 5-6 mein hoga)</div>';

  // analyst
  const A = D.analysis || {};
  const b = A.baseline;
  let ah = '';
  ah += `<div style="margin-bottom:10px"><span class="chip">metrics due <b>${A.due || 0}</b></span>` +
    (b ? `<span class="chip">baseline 2h (n=${b.n}) <b>${Math.round(b.views||0)}</b> views</span>
          <span class="chip">retention <b>${((b.avg_pct||0)*100).toFixed(0)}%</b></span>` 
       : '<span class="chip">baseline abhi nahi bana (3+ videos chahiye)</span>') + '</div>';
  if ((A.recent || []).length) {
    ah += (A.recent).map(r => `<div style="background:#0d1117;border-left:3px solid ${
      (r.flags||[]).length ? '#f85149' : '#3fb950'};padding:9px 12px;margin:7px 0;
      border-radius:0 6px 6px 0;font-size:12.5px">${esc(r.summary || '')}</div>`).join('');
  }
  const V = A.variables || {};
  if (Object.keys(V).length) {
    ah += '<table style="margin-top:10px"><tr><th>Variable</th><th>Best</th>' +
          '<th>Avg views</th><th>Retention</th><th>n</th></tr>' +
      Object.entries(V).map(([k, items]) => {
        const t = items[0];
        return `<tr><td>${k}</td><td><b>${esc(t.value)}</b></td>
          <td>${t.avg_views}</td><td>${(t.avg_retention*100).toFixed(0)}%</td>
          <td>${t.n}</td></tr>`;
      }).join('') + '</table>' +
      '<div style="color:#7d8590;font-size:11.5px;margin-top:8px">⚠️ Ye correlation hai, ' +
      'causation nahi. Proper A/B Scientist (Phase 8) karega.</div>';
  }
  document.getElementById('analyst').innerHTML = ah;

  // science
  document.getElementById('sci').innerHTML =
    expHtml() +
    (D.learnings.length ? `<table><tr><th>Variable</th><th>Winner</th><th>Loser</th>
      <th>Lift</th><th>n</th><th>Confidence</th></tr>
      ${D.learnings.map(l => `<tr><td>${l.variable}</td><td><b>${esc(l.winner)}</b></td>
      <td style="color:#6e7681">${esc(l.loser || '')}</td>
      <td style="color:${l.lift_pct > 0 ? '#3fb950' : '#f85149'}">${(l.lift_pct || 0).toFixed(0)}%</td>
      <td>${l.sample_size}</td><td>${l.confidence}</td></tr>`).join('')}</table>`
      : '<div style="color:#6e7681;margin-top:10px">Abhi koi learning nahi</div>') +
    (Object.keys((D.science || {}).champions || {}).length
      ? '<div style="margin-top:12px;font-size:12.5px"><b>Champions (ab default hain):</b> ' +
        Object.entries(D.science.champions).map(([k, c]) =>
          `<span class="chip">${k}=<b>${esc(c.value)}</b> ${c.lift_pct > 0 ? '+' : ''}${
            Math.round(c.lift_pct)}% (${c.confidence})</span>`).join(' ') + '</div>'
      : '');

  // logs
  document.getElementById('logs').innerHTML = D.logs.length
    ? D.logs.map(l => `<div class="lv-${l.level}">
        ${l.ts.slice(11, 19)} [${l.agent}] ${esc(l.msg)}</div>`).join('')
    : '<div style="color:#3fb950">Koi warning/error nahi 🎉</div>';
}

function expHtml() {
  const S = D.science || {}, E = S.evaluation, X = D.experiment;
  if (X) {
    const c = (E && E.videos_assigned) || {A: 0, B: 0};
    const m = (E && E.metrics_ready) || {A: 0, B: 0};
    let h = `<div style="margin-bottom:12px">
      <b>🧪 Experiment #${X.id}</b> — variable: <b>${esc(X.variable)}</b><br>
      <span style="color:#8b949e">${esc(X.hypothesis || '')}</span><br>
      <span class="chip">A: <b>${esc(X.arm_a)}</b> — ${c.A} videos, ${m.A} measured</span>
      <span class="chip">B: <b>${esc(X.arm_b)}</b> — ${c.B} videos, ${m.B} measured</span>
      <span class="chip">min ${X.min_per_arm}/arm</span></div>`;
    if (E && E.ready) {
      h += `<div style="background:#0d1117;border-left:3px solid ${
        E.significant ? '#3fb950' : '#e3b341'};padding:10px 13px;border-radius:0 6px 6px 0;
        font-size:12.5px;margin-bottom:10px">${esc(E.explanation)}<br>
        <b style="color:#58a6ff">➜ ${esc(E.recommendation)}</b></div>`;
      h += `<button class="ok" onclick="act('exp_conclude',0)">🏁 Conclude</button>`;
    } else if (E) {
      h += `<div style="color:#e3b341;font-size:12.5px;margin-bottom:10px">
        ${esc(E.message || E.status || '')}</div>`;
      h += `<button class="gr" onclick="if(confirm('Kam data pe conclude? Koi learning save nahi hogi.'))
        act('exp_conclude',0,{force:true})">Abandon</button>`;
    }
    return h;
  }
  const sg = S.suggestion;
  if (sg) {
    return `<div style="margin-bottom:12px;color:#8b949e">Koi experiment nahi chal raha.<br>
      <b style="color:#e6edf3">Suggestion:</b> <b>${esc(sg.variable)}</b> test karo —
      ${esc(sg.arm_a)} vs ${esc(sg.arm_b)}<br>
      <span style="font-size:12px">Kyun: ${esc(sg.reason)} · is sample size pe sirf
      ~${sg.mde_pct}%+ ka farq detect hoga</span></div>
      <button class="ok" onclick="act('exp_start',0,{variable:'${esc(sg.variable)}'})">
      🧪 Experiment shuru karo</button>`;
  }
  return '<div style="color:#6e7681;margin-bottom:12px">Koi experiment nahi chal raha</div>';
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
}

async function act(action, id, extra) {
  const r = await fetch('/api/action', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(Object.assign({action, video_id: id}, extra || {}))
  });
  const j = await r.json();
  if (action === 'validate' && j.report) {
    const el = document.getElementById('rep' + id);
    const f = j.report.facts;
    el.style.display = 'block';
    el.textContent = (j.report.ok ? '✅ PASS' : '❌ FAIL') + '  ' +
      `${f.resolution || '?'} · ${f.duration_sec || '?'}s · ${f.vcodec}+${f.acodec} · ` +
      `${f.lufs != null ? f.lufs + ' LUFS' : ''}\n` +
      (j.report.issues.length
        ? j.report.issues.map(i => `${i.level}: ${i.msg}` + (i.fix ? `\n   → ${i.fix}` : '')).join('\n')
        : 'Koi problem nahi mili 🎉');
    toast(j.report.ok ? 'Validate pass ✅' : 'Validate fail ❌', !j.report.ok);
    return load();
  }
  toast(j.msg || j.error || 'Done', !j.ok);
  load();
}

function generateVideo() {
  const topic = prompt('Video ka Topic daalein (ya auto topic ke liye khaali chhodein):');
  if (topic !== null) {
    act('generate', 0, {topic: topic.trim() || null});
  }
}

function rej(id) {
  const reason = prompt('Reject kyun kar rahe ho? (ye learning ban jayega)');
  if (reason !== null) act('reject', id, {reason});
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

load();
setInterval(() => {
  if (D && D.active_task && D.active_task.status === 'running') {
    load();
  }
}, 3000);
setInterval(load, 15000);
</script></body></html>
"""


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
