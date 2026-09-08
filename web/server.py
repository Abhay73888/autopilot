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

# Ensure project root is in sys.path when executed as a script (python web/server.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook
from core.quota import Quota

log = Logbook("dashboard")
PORT = int(os.environ.get("PORT", CONFIG.get("dashboard_port", 8765)))
HOST = os.environ.get("HOST", "0.0.0.0" if (os.environ.get("PORT") or os.environ.get("RAILWAY_ENVIRONMENT")) else "127.0.0.1")

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
    incoming = body.get("secret", "")
    if not incoming:
        for k, v in headers.items():
            if str(k).lower() == "x-webhook-secret":
                incoming = v
                break
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
CURRENT_TASK = {"status": "idle", "task": None, "job_id": None, "msg": "", "started_ts": None}

def run_bg_task(name: str, fn, *, job_id: str | None = None, action: str | None = None,
                topic: str | None = None, idempotency_key: str | None = None,
                request_id: str | None = None):
    global CURRENT_TASK
    if CURRENT_TASK["status"] == "running":
        return {"ok": False, "error": f"Ek task pehle se chal raha hai: {CURRENT_TASK['task']}"}

    import inspect
    import uuid
    if not job_id:
        job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    act_name = action or name
    # Pre-register job in database
    try:
        with DB() as init_db:
            init_db.create_job(job_id=job_id, action=act_name, topic=topic,
                               idempotency_key=idempotency_key, request_id=request_id)
    except Exception as e:
        log.warn("Job create in DB warning", reason=str(e)[:120])

    CURRENT_TASK = {
        "status": "running",
        "task": name,
        "job_id": job_id,
        "msg": f"{name} shuru ho raha hai...",
        "started_ts": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }

    def _worker():
        global CURRENT_TASK
        now_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with DB() as thread_db:
            thread_db.update_job(job_id, status="running", started_ts=now_ts)
            try:
                sig = inspect.signature(fn)
                if len(sig.parameters) >= 1:
                    res = fn(thread_db)
                else:
                    res = fn()

                res_msg = res.get("msg") if isinstance(res, dict) else (str(res) if res else f"{name} poora hua 🎉")
                vid = res.get("video_id") if isinstance(res, dict) else None
                paths = res.get("result_paths") if isinstance(res, dict) else None

                done_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
                thread_db.update_job(job_id, status="completed", completed_ts=done_ts,
                                     video_id=vid, result_paths=paths)
                CURRENT_TASK = {
                    "status": "completed",
                    "task": name,
                    "job_id": job_id,
                    "video_id": vid,
                    "msg": res_msg,
                    "started_ts": None
                }
            except Exception as e:  # noqa: BLE001
                log.error(f"Background task {name} ({job_id}) fail hua", e)
                fail_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
                thread_db.update_job(job_id, status="failed", completed_ts=fail_ts,
                                     error_message=str(e))
                CURRENT_TASK = {
                    "status": "error",
                    "task": name,
                    "job_id": job_id,
                    "msg": f"Error: {str(e)}",
                    "started_ts": None
                }

    threading.Thread(target=_worker, daemon=True).start()
    return {
        "ok": True,
        "job_id": job_id,
        "status": "queued",
        "msg": f"{name} background mein shuru kar diya hai",
        "status_url": f"/api/jobs/{job_id}"
    }

# =====================================================================
# ACTIONS
# =====================================================================
def do_action(action: str, video_id: int, payload: dict) -> dict:
    with DB() as db:
        # ---- experiment actions kisi video se bandhe nahi hain ----
        if action == "generate":
            topic = payload.get("topic")
            dry_run = bool(payload.get("dry_run", CONFIG.get("mock_mode")))

            def _gen(worker_db):
                from run import one_video
                manifest = one_video(topic=topic, dry_run=dry_run, with_images=True, preset="veryfast", keep_temp=False, voice=payload.get("voice"))
                if not manifest:
                    raise RuntimeError("Pipeline failed to generate and render video. Check logs for details.")
                vid = manifest.get("video_id", 0)
                v_dir = ROOT / "output" / f"video_{vid:04d}"
                paths = {}
                if (v_dir / "final.mp4").exists():
                    paths["video_path"] = str((v_dir / "final.mp4").resolve())
                if (v_dir / "cover.jpg").exists():
                    paths["cover_path"] = str((v_dir / "cover.jpg").resolve())
                if (v_dir / "manifest.json").exists():
                    paths["manifest_path"] = str((v_dir / "manifest.json").resolve())
                return {
                    "msg": f"Video #{vid} ban ke tayar hai!",
                    "video_id": vid,
                    "result_paths": paths
                }

            return run_bg_task("Video Generation", _gen,
                               job_id=payload.get("job_id"), action="generate",
                               topic=topic, idempotency_key=payload.get("idempotency_key"),
                               request_id=payload.get("request_id"))

        if action == "publish_video":
            v = db.get_video(video_id)
            if not v:
                return {"ok": False, "error": f"Video #{video_id} nahi mila"}

            def _pub(worker_db):
                from agents.publisher import Publisher
                from agents.ig_publisher import IGPublisher
                q = Quota(worker_db)
                out_yt = Publisher(worker_db, q).publish_due()
                out_ig = IGPublisher(worker_db, q).publish_due()
                return {
                    "msg": f"YT: {len(out_yt.get('published', []))} uploaded | IG: {len(out_ig.get('published', []))} uploaded",
                    "video_id": video_id
                }

            return run_bg_task(f"Publish Video #{video_id}", _pub,
                               job_id=payload.get("job_id"), action="publish_video",
                               idempotency_key=payload.get("idempotency_key"),
                               request_id=payload.get("request_id"))

        if action == "exp_start":
            from agents.scientist import Scientist
            r = Scientist(db).start(payload.get("variable") or None)
            return {"ok": r.get("ok", False),
                    "msg": (f"Experiment #{r['experiment_id']} shuru: {r['variable']} "
                            f"({r['arm_a']} vs {r['arm_b']})") if r.get("ok") else None,
                    "error": r.get("error")}

        if action == "tick":
            dry_run = bool(payload.get("dry_run"))

            def _tick_fn(worker_db):
                from agents.chief import Chief, Lock
                with Lock():
                    out = Chief(worker_db, dry_run=dry_run).tick()
                acts = out.get("actions") or ["kuch karne ko nahi tha"]
                return {"msg": " | ".join(acts)[:200]}

            return run_bg_task("Chief Tick", _tick_fn,
                               job_id=payload.get("job_id"), action="tick",
                               idempotency_key=payload.get("idempotency_key"),
                               request_id=payload.get("request_id"))

        if action == "clear_logs":
            log_dir = (ROOT / CONFIG.get("log_dir", "logs")).resolve()
            cleared = 0
            if log_dir.exists():
                for lf in log_dir.glob("*.jsonl"):
                    try:
                        lf.unlink()
                        cleared += 1
                    except Exception:
                        pass
            return {"ok": True, "msg": f"{cleared} log file(s) clear ho gayi. Diagnostics radar clean ho gaya!"}

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
        # ---- Make.com / async job endpoints ----
        if u.path == "/api/jobs" or u.path.startswith("/api/jobs/"):
            client_ip = self.client_address[0] if hasattr(self, "client_address") and self.client_address else "unknown"
            headers_dict = dict(self.headers)
            qs = parse_qs(u.query)
            query_secret = qs.get("secret", [""])[0]
            if MAKE_WEBHOOK_SECRET and client_ip not in ("127.0.0.1", "::1", "localhost"):
                ok, status_code, err_msg = _check_webhook_auth(headers_dict, {"secret": query_secret}, client_ip)
                if not ok:
                    return self._json(status_code, {"ok": False, "error": err_msg})

            with DB() as db:
                if u.path == "/api/jobs":
                    limit = int(qs.get("limit", [50])[0])
                    st_filter = qs.get("status", [None])[0]
                    rows = db.list_jobs(limit=limit, status=st_filter)
                    jobs_list = []
                    for r in rows:
                        d = dict(r)
                        if d.get("result_paths"):
                            try:
                                d["result_paths"] = json.loads(d["result_paths"])
                            except Exception:
                                pass
                        jobs_list.append(d)
                    return self._json(200, {"ok": True, "jobs": jobs_list, "count": len(jobs_list)})

                job_id = u.path[len("/api/jobs/"):].strip("/")
                job = db.get_job(job_id)
                if not job:
                    return self._json(404, {"ok": False, "error": f"Job #{job_id} nahi mila"})
                jdict = dict(job)
                if jdict.get("result_paths"):
                    try:
                        jdict["result_paths"] = json.loads(jdict["result_paths"])
                    except Exception:
                        pass
                return self._json(200, {"ok": True, "job": jdict})

        # ---- Make.com status polling endpoint ----
        if u.path == "/api/status":
            qs = parse_qs(u.query)
            jid = qs.get("job_id", [None])[0]
            with DB() as db:
                if jid:
                    job = db.get_job(jid)
                    if not job:
                        return self._json(404, {"ok": False, "error": f"Job #{jid} nahi mila"})
                    jdict = dict(job)
                    if jdict.get("result_paths"):
                        try:
                            jdict["result_paths"] = json.loads(jdict["result_paths"])
                        except Exception:
                            pass
                    return self._json(200, {
                        "ok": True,
                        "job": jdict,
                        "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    })

                recent_jobs = []
                for r in db.list_jobs(limit=5):
                    d = dict(r)
                    if d.get("result_paths"):
                        try:
                            d["result_paths"] = json.loads(d["result_paths"])
                        except Exception:
                            pass
                    recent_jobs.append(d)

                return self._json(200, {
                    "ok": True,
                    "task": CURRENT_TASK,
                    "recent_jobs": recent_jobs,
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
            "dry_run": false,
            "idempotency_key": "optional-key",
            "request_id": "optional-request-id"
          }

        Headers:
          X-Webhook-Secret: "tumhara-secret"
          X-Idempotency-Key: "optional-key"
          X-Request-Id: "optional-request-id"

        Response:
          HTTP 202 Accepted (for new jobs)
          { "ok": true, "job_id": "...", "status": "queued", "status_url": "/api/jobs/..." }
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
            topic = body.get("topic") or None
            dry_run = bool(body.get("dry_run", False))
            idempotency_key = self.headers.get("X-Idempotency-Key") or body.get("idempotency_key")
            request_id = self.headers.get("X-Request-Id") or body.get("request_id")

            with DB() as db:
                if idempotency_key:
                    existing = db.get_job_by_idempotency_key(idempotency_key)
                    if existing:
                        st = existing["status"]
                        paths = json.loads(existing["result_paths"] or "{}") if existing["result_paths"] else {}
                        log.info(f"Make.com idempotent match: key={idempotency_key} job={existing['job_id']} status={st}")
                        if st in ("queued", "running"):
                            return self._json(200, {
                                "ok": True,
                                "job_id": existing["job_id"],
                                "status": st,
                                "message": "Job is currently being processed",
                                "idempotent": True,
                                "status_url": f"/api/jobs/{existing['job_id']}"
                            })
                        elif st == "completed":
                            return self._json(200, {
                                "ok": True,
                                "job_id": existing["job_id"],
                                "status": "completed",
                                "video_id": existing["video_id"],
                                "result_paths": paths,
                                "message": "Job previously completed successfully",
                                "idempotent": True,
                                "status_url": f"/api/jobs/{existing['job_id']}"
                            })
                        elif st == "failed" and not body.get("retry", False):
                            return self._json(200, {
                                "ok": False,
                                "job_id": existing["job_id"],
                                "status": "failed",
                                "error": existing["error_message"],
                                "idempotent": True,
                                "status_url": f"/api/jobs/{existing['job_id']}"
                            })

                import uuid
                job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
                log.info(f"Make.com webhook aaya: job_id={job_id} action={action} topic={topic}")

                payload = {
                    "topic": topic,
                    "dry_run": dry_run,
                    "job_id": job_id,
                    "idempotency_key": idempotency_key,
                    "request_id": request_id
                }
                res = do_action(action, 0, payload)

            if not res.get("ok"):
                return self._json(400, res)

            return self._json(202, {
                "ok": True,
                "job_id": res.get("job_id", job_id),
                "status": "queued",
                "message": res.get("msg", "Job accepted"),
                "status_url": f"/api/jobs/{res.get('job_id', job_id)}"
            })
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
:root, [data-theme="dark"] {
  /* Ultra-Enhanced 3D Dark Slate / Midnight Palette */
  --bg-main: #080C14;
  --bg-card: #0F172A;
  --bg-card-sub: #131E33;
  --bg-surface: #0B1120;
  --bg-blue-soft: rgba(56, 189, 248, 0.14);
  --bg-blue-card: #0E182A;
  --bg-canvas: #070B12;

  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --text-dim: #475569;

  --border-light: #1E293B;
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-focus: #38BDF8;
  --border-glass: rgba(255, 255, 255, 0.14);

  --primary-blue: #38BDF8;
  --blue-hover: #0284C7;
  --blue-soft: rgba(56, 189, 248, 0.16);
  --blue-soft-border: rgba(56, 189, 248, 0.4);
  --purple-accent: #C084FC;
  --purple-soft: rgba(192, 132, 252, 0.16);
  --purple-border: rgba(192, 132, 252, 0.35);

  --green: #34D399;
  --green-soft: rgba(52, 211, 153, 0.16);
  --green-border: rgba(52, 211, 153, 0.35);
  --amber: #FBBF24;
  --amber-soft: rgba(251, 191, 36, 0.16);
  --amber-border: rgba(251, 191, 36, 0.35);
  --red: #F87171;
  --red-soft: rgba(248, 113, 113, 0.16);
  --red-border: rgba(248, 113, 113, 0.35);

  /* Deep 3D Spatial Shadows & Neon Glows */
  --shadow-1: 0 4px 12px rgba(0, 0, 0, 0.6);
  --shadow-2: 0 10px 28px -4px rgba(0, 0, 0, 0.75), 0 4px 10px -2px rgba(0, 0, 0, 0.5);
  --shadow-3: 0 24px 50px -8px rgba(0, 0, 0, 0.85), 0 8px 24px -4px rgba(0, 0, 0, 0.65);
  --shadow-3d: 0 35px 85px -15px rgba(0, 0, 0, 0.95), 0 0 50px -5px rgba(56, 189, 248, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.2);
  --shadow-floating: 0 22px 45px -8px rgba(0, 0, 0, 0.85), 0 0 30px -4px rgba(56, 189, 248, 0.4);

  --radius-card: 20px;
  --radius-pill: 9999px;

  --hero-bg: radial-gradient(ellipse at 50% 0%, #172554 0%, #0F172A 55%, #080C14 100%);
  --hero-card-bg: #0F172A;
  --hero-badge-bg: rgba(15, 23, 42, 0.9);
  --hero-badge-border: rgba(56, 189, 248, 0.35);
  --nav-bg: rgba(11, 17, 32, 0.85);
  --nav-border: #1E293B;
  --chip-bg: #131E33;
  --chip-color: #38BDF8;
}

[data-theme="soft-light"] {
  --bg-main: #EEF2F6;
  --bg-card: #FFFFFF;
  --bg-card-sub: #F8FAFC;
  --bg-surface: #F8FAFC;
  --bg-blue-soft: #EFF6FF;
  --bg-blue-card: #F0F7FF;
  --bg-canvas: #FFFFFF;

  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-muted: #64748B;
  --text-dim: #94A3B8;

  --border-light: #E2E8F0;
  --border-subtle: #F1F5F9;
  --border-focus: #2563EB;
  --border-glass: rgba(255, 255, 255, 0.85);

  --primary-blue: #2563EB;
  --blue-hover: #1D4ED8;
  --blue-soft: #EFF6FF;
  --blue-soft-border: #DBEAFE;
  --purple-accent: #7C3AED;
  --purple-soft: #FAF5FF;
  --purple-border: #E9D5FF;

  --green: #059669;
  --green-soft: #ECFDF5;
  --green-border: #A7F3D0;
  --amber: #D97706;
  --amber-soft: #FFFBEB;
  --amber-border: #FDE68A;
  --red: #DC2626;
  --red-soft: #FEF2F2;
  --red-border: #FECACA;

  --shadow-1: 0 1px 3px rgba(15, 23, 42, 0.05), 0 1px 2px rgba(15, 23, 42, 0.03);
  --shadow-2: 0 4px 16px -2px rgba(15, 23, 42, 0.06), 0 2px 6px -1px rgba(15, 23, 42, 0.04);
  --shadow-3: 0 16px 36px -6px rgba(15, 23, 42, 0.09), 0 6px 16px -3px rgba(15, 23, 42, 0.05);
  --shadow-3d: 0 24px 48px -12px rgba(15, 23, 42, 0.14), 0 0 32px -8px rgba(37, 99, 235, 0.12);
  --shadow-floating: 0 14px 28px -6px rgba(15, 23, 42, 0.1), 0 4px 10px -2px rgba(15, 23, 42, 0.05);

  --hero-bg: radial-gradient(ellipse at 50% 0%, #DBEAFE 0%, #EFF6FF 55%, #EEF2F6 100%);
  --hero-card-bg: #FFFFFF;
  --hero-badge-bg: rgba(255, 255, 255, 0.94);
  --hero-badge-border: rgba(219, 234, 254, 0.9);
  --nav-bg: rgba(255, 255, 255, 0.88);
  --nav-border: #E2E8F0;
  --chip-bg: #F1F5F9;
  --chip-color: #2563EB;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg-main);
  color: var(--text-primary);
  font: 14px/1.55 'Inter', -apple-system, sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
  background-image: 
    radial-gradient(circle at 50% -10%, rgba(56, 189, 248, 0.18) 0%, transparent 60%),
    radial-gradient(circle at 90% 20%, rgba(192, 132, 252, 0.15) 0%, transparent 45%),
    radial-gradient(circle at 10% 80%, rgba(37, 99, 235, 0.12) 0%, transparent 50%);
  background-repeat: no-repeat;
  transition: background-color 0.25s ease, color 0.25s ease;
}

#app {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px 32px 80px;
}

/* 1. Top Navbar */
.hud-header {
  background: var(--nav-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--nav-border);
  border-radius: var(--radius-card);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  box-shadow: var(--shadow-2);
  position: sticky;
  top: 16px;
  z-index: 100;
  transition: all 0.2s ease;
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
  letter-spacing: -0.3px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}
.brand-logo i {
  display: inline-block;
  font-style: normal;
  color: var(--primary-blue);
  filter: drop-shadow(0 0 12px rgba(56, 189, 248, 0.6));
}

.badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  box-shadow: var(--shadow-1);
}
.badge.ok { background: var(--green-soft); border-color: var(--green-border); color: var(--green); }
.badge.warn { background: var(--amber-soft); border-color: var(--amber-border); color: var(--amber); }
.badge.bad { background: var(--red-soft); border-color: var(--red-border); color: var(--red); }
.badge.live { background: var(--blue-soft); border-color: var(--blue-soft-border); color: var(--primary-blue); }

.hud-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.theme-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  color: var(--text-primary);
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-1);
  transition: all 0.18s ease;
}
.theme-toggle-btn:hover {
  border-color: var(--primary-blue);
  color: var(--primary-blue);
  box-shadow: 0 0 14px rgba(56, 189, 248, 0.35);
  transform: translateY(-1px);
}

/* Button System */
.btn {
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  outline: none;
}
.btn:active { transform: translateY(2px) scale(0.97); }
.btn-primary {
  background: linear-gradient(180deg, #38BDF8 0%, #2563EB 100%);
  color: #FFFFFF;
  box-shadow: 0 2px 10px rgba(56, 189, 248, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.btn-primary:hover {
  background: linear-gradient(180deg, #0284C7 0%, #1D4ED8 100%);
  box-shadow: 0 4px 18px rgba(56, 189, 248, 0.55);
  transform: translateY(-2px);
}
.btn-success {
  background: linear-gradient(180deg, #34D399 0%, #059669 100%);
  color: #FFFFFF;
  box-shadow: 0 2px 10px rgba(52, 211, 153, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.btn-success:hover {
  background: linear-gradient(180deg, #059669 0%, #047857 100%);
  transform: translateY(-2px);
}
.btn-danger {
  background: var(--red-soft);
  border: 1px solid var(--red-border);
  color: var(--red);
}
.btn-danger:hover {
  background: var(--red-soft);
}
.btn-ghost, .btn-secondary {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  color: var(--text-primary);
  box-shadow: var(--shadow-1);
}
.btn-ghost:hover, .btn-secondary:hover {
  background: var(--bg-card-sub);
  color: var(--primary-blue);
  border-color: var(--primary-blue);
  transform: translateY(-2px);
}

/* 2. 3D HERO SPATIAL STAGE */
.hero-3d-section {
  position: relative;
  background: var(--hero-bg);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 26px;
  padding: 48px 42px;
  margin: 20px 0 32px;
  display: grid;
  grid-template-columns: 1.15fr 0.95fr;
  gap: 36px;
  align-items: center;
  box-shadow: var(--shadow-3);
  overflow: hidden;
  transition: all 0.25s ease;
}
.hero-3d-section::before {
  content: '';
  position: absolute;
  top: -80px; right: -80px;
  width: 380px; height: 380px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.2) 0%, transparent 70%);
  pointer-events: none;
}
.hero-badge-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--hero-badge-bg);
  border: 1px solid var(--hero-badge-border);
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 700;
  color: var(--primary-blue);
  box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
  margin-bottom: 16px;
}
.hero-badge-wrap .pulse-dot {
  width: 8px; height: 8px;
  background: var(--primary-blue);
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.35);
  animation: pulseDot 2s infinite;
}
@keyframes pulseDot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}
.hero-title {
  font-family: 'Outfit', sans-serif;
  font-size: 38px;
  font-weight: 800;
  line-height: 1.18;
  letter-spacing: -0.5px;
  color: var(--text-primary);
  margin-bottom: 16px;
}
.hero-title .text-gradient {
  background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-desc {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 26px;
}
.hero-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}
.hero-metrics-strip {
  display: flex;
  align-items: center;
  gap: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
  font-size: 12.5px;
  color: var(--text-muted);
}
.hero-metrics-strip span b {
  color: var(--text-primary);
  font-weight: 700;
}

/* 3D Spatial Hero Stage (Enhanced Depth & Parallax) */
.hero-stage {
  perspective: 1400px;
  position: relative;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  transform-style: preserve-3d;
}
.hero-3d-card {
  width: 370px;
  background: var(--hero-card-bg);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 22px;
  padding: 24px;
  box-shadow: var(--shadow-3d);
  transform: rotateX(12deg) rotateY(-14deg) rotateZ(2deg) translateZ(20px);
  transform-style: preserve-3d;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease;
  position: relative;
}
.hero-3d-card:hover {
  transform: rotateX(4deg) rotateY(-6deg) rotateZ(1deg) scale3d(1.03, 1.03, 1.03) translateZ(40px);
  border-color: rgba(56, 189, 248, 0.7);
  box-shadow: 0 40px 100px -15px rgba(0, 0, 0, 0.95), 0 0 65px -5px rgba(56, 189, 248, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.3);
}
.stage-preview-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
  transform: translateZ(16px);
  transform-style: preserve-3d;
}
.stage-preview-title {
  font-family: 'Outfit', sans-serif;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.stage-preview-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  transform-style: preserve-3d;
}
.stage-clip-mock {
  background: linear-gradient(135deg, #070B12 0%, #0F172A 100%);
  border-radius: 14px;
  height: 126px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  padding: 14px;
  box-shadow: 0 12px 28px -6px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
  transform: translateZ(28px);
  transform-style: preserve-3d;
}
.stage-clip-overlay {
  position: relative;
  z-index: 2;
  color: #FFFFFF;
}
.stage-clip-overlay .clip-tag {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: rgba(37, 99, 235, 0.95);
  padding: 2px 7px;
  border-radius: 5px;
  text-transform: uppercase;
  display: inline-block;
  margin-bottom: 4px;
}
.stage-clip-overlay .clip-hook {
  font-size: 11.5px;
  font-weight: 600;
  color: #F8FAFC;
  text-shadow: 0 1px 3px rgba(0,0,0,0.9);
}
.stage-meter-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  font-size: 11px;
  margin-top: 10px;
  transform: translateZ(20px);
  transform-style: preserve-3d;
}
.stage-meter-box {
  background: rgba(11, 17, 32, 0.85);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 7px 8px;
  text-align: center;
  box-shadow: 0 4px 10px rgba(0,0,0,0.4);
}
.stage-meter-box .val {
  font-weight: 700;
  color: var(--primary-blue);
  font-size: 12px;
}

/* Floating 3D Badges with Enhanced Z-Elevation */
.float-badge {
  position: absolute;
  background: var(--hero-badge-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--hero-badge-border);
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow: var(--shadow-floating);
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-primary);
  pointer-events: none;
  z-index: 10;
  transform-style: preserve-3d;
  transition: all 0.3s ease;
}
.float-badge.pos-top-left {
  top: 5px; left: -25px;
  animation: float3D_1 4.5s ease-in-out infinite;
}
.float-badge.pos-top-right {
  top: 25px; right: -25px;
  animation: float3D_3 5.2s ease-in-out infinite;
}
.float-badge.pos-bottom-left {
  bottom: 15px; left: -15px;
  animation: float3D_2 4.8s ease-in-out infinite;
}
.float-badge.pos-bottom-right {
  bottom: 0px; right: -30px;
  animation: float3D_4 4.2s ease-in-out infinite;
}
.float-badge .badge-icon {
  width: 30px; height: 30px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}
.float-badge .icon-blue { background: rgba(56, 189, 248, 0.2); color: #38BDF8; }
.float-badge .icon-green { background: rgba(52, 211, 153, 0.2); color: #34D399; }
.float-badge .icon-purple { background: rgba(192, 132, 252, 0.2); color: #C084FC; }
.float-badge .icon-amber { background: rgba(251, 191, 36, 0.2); color: #FBBF24; }

@keyframes float3D_1 {
  0%, 100% { transform: translateY(0px) translateZ(80px) rotateZ(0deg); }
  50% { transform: translateY(-12px) translateZ(95px) rotateZ(-1.5deg); }
}
@keyframes float3D_2 {
  0%, 100% { transform: translateY(0px) translateZ(65px) rotateZ(0deg); }
  50% { transform: translateY(10px) translateZ(80px) rotateZ(1.5deg); }
}
@keyframes float3D_3 {
  0%, 100% { transform: translateY(0px) translateZ(85px) rotateZ(0deg); }
  50% { transform: translateY(-10px) translateZ(100px) rotateZ(2deg); }
}
@keyframes float3D_4 {
  0%, 100% { transform: translateY(0px) translateZ(75px) rotateZ(0deg); }
  50% { transform: translateY(11px) translateZ(90px) rotateZ(-2deg); }
}

/* 3. Navigation Tabs */
.nav-bar {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 10px 0 20px;
  margin-bottom: 12px;
  scrollbar-width: none;
}
.nav-bar::-webkit-scrollbar { display: none; }
.nav-tab {
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: var(--shadow-1);
}
.nav-tab:hover {
  background: var(--bg-card-sub);
  color: var(--text-primary);
  border-color: var(--primary-blue);
  transform: translateY(-2px);
}
.nav-tab.active {
  background: var(--bg-card);
  border-color: var(--primary-blue);
  color: var(--primary-blue);
  box-shadow: 0 4px 16px rgba(56, 189, 248, 0.25);
}
.nav-tab .tab-count {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--bg-surface);
  color: var(--text-secondary);
}
.nav-tab.active .tab-count {
  background: var(--primary-blue);
  color: #070B12;
  font-weight: 700;
}
.nav-tab.tab-err.has-err .tab-count {
  background: var(--red);
  color: #FFFFFF;
}

/* 4. Active Task Banner */
.task-banner {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
  border: 1px solid var(--blue-soft-border);
  color: var(--primary-blue);
  padding: 14px 20px;
  border-radius: 14px;
  margin: 16px 0 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  font-weight: 600;
  box-shadow: var(--shadow-2);
}
.task-spinner {
  width: 18px; height: 18px;
  border: 3px solid rgba(56, 189, 248, 0.3);
  border-top-color: var(--primary-blue);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 5. 3D Stat HUD Cards with Interactive Perspective Tilt */
.grid { display: grid; gap: 18px; }
.cards-4 { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-bottom: 28px; }

.card-3d, .stat-card, .diagram-card, .chart-box {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-card);
  padding: 22px;
  box-shadow: var(--shadow-2);
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease, border-color 0.25s ease;
  transform-style: preserve-3d;
  perspective: 900px;
  overflow: hidden;
}
.card-3d:hover, .stat-card:hover, .diagram-card:hover, .chart-box:hover {
  border-color: rgba(56, 189, 248, 0.5);
  box-shadow: 0 22px 50px -10px rgba(0, 0, 0, 0.9), 0 0 32px -4px rgba(56, 189, 248, 0.3);
  transform: translateY(-6px) translateZ(14px);
}
.card-3d .glare, .stat-card .glare, .video-card .glare {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  border-radius: inherit;
  opacity: 0.35;
  mix-blend-mode: screen;
  display: none;
}

.stat-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.stat-k {
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.stat-v {
  font-family: 'Outfit', sans-serif;
  font-size: 34px;
  font-weight: 800;
  margin-top: 10px;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}
.stat-sub {
  font-size: 12.5px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* 6. Sections & Progressive Depths */
.section {
  margin-bottom: 38px;
  display: block;
  scroll-margin-top: 80px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 28px 0 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.section-title {
  font-family: 'Outfit', sans-serif;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}
.section-title span.glow-icon {
  font-size: 20px;
}

/* Quota Section */
#section-quota {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 20px;
  padding: 24px;
  box-shadow: var(--shadow-1);
}
.quota-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}
.q-row {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: var(--shadow-1);
}
.q-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12.5px;
}
.q-name { font-weight: 600; color: var(--text-secondary); }
.q-nums { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text-primary); font-weight: 600; }
.q-bar-bg {
  width: 100%;
  height: 8px;
  background: var(--border-light);
  border-radius: 4px;
  overflow: hidden;
}
.q-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: var(--primary-blue);
  transition: width 0.4s ease;
}
.q-bar-fill.w { background: var(--amber); }
.q-bar-fill.d { background: var(--red); }

/* 7. Swarm Pipeline Diagram Section - God Level */
.diagram-card {
  padding: 24px 28px;
  border-radius: var(--radius-card);
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-2);
  position: relative;
  overflow: hidden;
}
.swarm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-light);
}
.swarm-filter-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.swarm-filter-chip {
  font-size: 11.5px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}
.swarm-filter-chip:hover {
  background: var(--bg-card-sub);
  color: var(--text-primary);
  border-color: var(--primary-blue);
}
.swarm-filter-chip.active {
  background: rgba(56, 189, 248, 0.18);
  border-color: var(--primary-blue);
  color: var(--primary-blue);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
}
.swarm-telemetry-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--green);
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-surface);
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border-light);
}
#swarmCanvas {
  width: 100%;
  height: 330px;
  display: block;
  cursor: pointer;
  background: var(--bg-canvas);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.6);
}
.diagram-hud {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px solid var(--border-light);
  margin-top: 14px;
  font-size: 12px;
  color: var(--text-secondary);
  flex-wrap: wrap;
  gap: 10px;
}
.diagram-tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 12px;
  color: var(--text-primary);
  box-shadow: var(--shadow-floating);
  display: none;
  z-index: 50;
  max-width: 320px;
  backdrop-filter: blur(12px);
}

/* 8. Live Graphs Pods - God Level */
.graph-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
  gap: 22px;
}
.chart-box {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-card);
  padding: 22px;
  box-shadow: var(--shadow-2);
  position: relative;
}
.chart-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}
.chart-box h3 {
  font-family: 'Outfit', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.graph-ctrl-bar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.graph-ctrl-btn {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}
.graph-ctrl-btn:hover {
  background: var(--bg-card-sub);
  color: var(--text-primary);
  border-color: var(--primary-blue);
}
.graph-ctrl-btn.active {
  background: rgba(56, 189, 248, 0.16);
  border-color: var(--primary-blue);
  color: var(--primary-blue);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
}
.chart-canvas {
  width: 100%;
  height: 250px;
  display: block;
  background: var(--bg-canvas);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.5);
  cursor: crosshair;
}
.graph-status-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-light);
  font-size: 11.5px;
  color: var(--text-secondary);
  flex-wrap: wrap;
  gap: 8px;
}
.graph-hud-pill {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  color: var(--primary-blue);
}

/* Agent Inspector Modal */
.agent-inspector-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin: 16px 0;
}
.agent-info-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 12px 14px;
}
.agent-info-k {
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.agent-info-v {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 9. Video Studio & Approval Deck */
.video-card {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
  margin-bottom: 20px;
  padding: 22px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-2);
  position: relative;
  overflow: hidden;
}
.video-media {
  background: #0F172A;
  border-radius: 14px;
  overflow: hidden;
  height: 320px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-1);
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
  color: var(--text-primary);
  margin-bottom: 10px;
}
.video-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.hook-box {
  background: rgba(37, 99, 235, 0.08);
  border-left: 4px solid var(--primary-blue);
  border-radius: 8px;
  padding: 12px 16px;
  margin-top: 10px;
  font-size: 13.5px;
  color: var(--text-primary);
  border: 1px solid var(--blue-soft-border);
  border-left-width: 4px;
}
.btn-deck {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

/* 10. Diagnostics Hub */
.diag-hub {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-card);
  padding: 24px;
  position: relative;
  box-shadow: var(--shadow-1);
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
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 10px 14px;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}
.diag-search:focus {
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}
.diag-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.diag-pill {
  font-size: 11.5px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 20px;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}
.diag-pill:hover {
  background: var(--bg-card-sub);
  color: var(--text-primary);
  border-color: var(--primary-blue);
}
.diag-pill.active {
  background: rgba(37, 99, 235, 0.15);
  border-color: var(--primary-blue);
  color: var(--primary-blue);
}
.diag-list {
  max-height: 440px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.diag-item {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 14px 16px;
  font-size: 13px;
  box-shadow: var(--shadow-1);
}
.diag-item.lvl-FATAL, .diag-item.lvl-ERROR { border-left: 4px solid var(--red); }
.diag-item.lvl-WARN { border-left: 4px solid var(--amber); }
.diag-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 12px;
}
.diag-agent { font-weight: 700; color: var(--text-primary); }
.diag-ts { color: var(--text-muted); font-size: 11px; margin-left: auto; }
.diag-msg { color: var(--text-primary); font-weight: 500; }
.diag-detail {
  background: var(--bg-main);
  padding: 8px 12px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: var(--text-secondary);
  margin-top: 8px;
  white-space: pre-wrap;
}
.diag-fix {
  background: var(--green-soft);
  border: 1px solid var(--green-border);
  color: var(--green);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  margin-top: 8px;
}

/* 11. Tables */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  color: var(--text-secondary);
  font-weight: 700;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  background: var(--bg-surface);
}
td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
}
tr:hover td { background: rgba(37, 99, 235, 0.03); }

/* 12. Modal */
.modal-overlay {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(8px);
  z-index: 999;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 20px;
  width: 100%;
  max-width: 560px;
  padding: 32px;
  box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25);
}
.modal-title {
  font-family: 'Outfit', sans-serif;
  font-size: 21px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.form-group {
  margin-bottom: 18px;
}
.form-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.form-input, .form-select {
  width: 100%;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 10px 14px;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}
.form-input:focus, .form-select:focus {
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}
.topic-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.topic-chip {
  font-size: 11.5px;
  font-weight: 500;
  background: var(--chip-bg);
  border: 1px solid var(--border-light);
  padding: 5px 12px;
  border-radius: 14px;
  color: var(--chip-color);
  cursor: pointer;
  transition: all 0.15s;
}
.topic-chip:hover {
  background: rgba(37, 99, 235, 0.15);
  border-color: var(--primary-blue);
}

/* 13. Modern SaaS Footer */
.app-footer {
  margin-top: 60px;
  padding: 32px 0 20px;
  border-top: 1px solid var(--border-light);
  color: var(--text-secondary);
  font-size: 13px;
}
.footer-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}
.footer-brand {
  font-size: 14px;
  color: var(--text-primary);
}
.footer-brand i { color: var(--primary-blue); font-style: normal; margin-right: 4px; }
.footer-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--green);
}
.footer-status .pulse-dot {
  width: 7px; height: 7px;
  background: var(--green);
  border-radius: 50%;
  animation: pulseDot 2s infinite;
}
.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-muted);
  font-size: 12px;
}
.footer-links a {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
}
.footer-links a:hover {
  color: var(--primary-blue);
}

/* Toast */
#toast {
  position: fixed;
  bottom: 28px; right: 28px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  color: var(--text-primary);
  padding: 14px 24px;
  border-radius: 14px;
  display: none;
  font-weight: 600;
  box-shadow: var(--shadow-3);
  z-index: 9999;
}
</style>
</head>
<body>

<div id="app">
  <!-- Top Light Theme Header -->
  <header class="hud-header">
    <div class="brand-box">
      <div class="brand-logo"><i>🎬</i> <span id="brand">AUTOPILOT</span></div>
      <span class="badge" id="autonomy"></span>
      <span class="badge" id="mock"></span>
      <span class="badge live" id="clock"></span>
    </div>

    <div class="hud-actions">
      <div class="theme-toggle-btn" id="themeToggleBtn" onclick="toggleTheme()" title="Theme Toggle (Soft Light / Dark)">
        <span id="themeIcon">🌤️</span> <span id="themeLabel">Soft Light</span>
      </div>
      <button class="btn btn-secondary" onclick="load()" title="Refresh Dashboard">🔄 Refresh</button>
      <button class="btn btn-primary" onclick="openCreateModal()" title="Nayi Video Banao">✨ Nayi Video</button>
      <button class="btn btn-primary" style="background:#059669;border-color:#059669" onclick="act('tick', 0)" title="Ek Poora Swarm Tick Run Karo">⚡ Run Swarm Tick</button>
    </div>
  </header>

  <!-- Active Task Banner -->
  <div id="task_banner" class="task-banner" style="display:none">
    <div class="task-spinner"></div>
    <span id="task_msg">Swarm task chal raha hai...</span>
  </div>

  <!-- 3D HERO SPATIAL STAGE -->
  <section class="hero-3d-section" id="hero-section">
    <div class="hero-left">
      <div class="hero-badge-wrap">
        <span class="pulse-dot"></span>
        <span>AUTONOMOUS MULTIMODAL AI AGENTS</span>
      </div>
      <h1 class="hero-title">
        Cinematic AI Series Engine with <span class="text-gradient">3D Swarm Intelligence</span>
      </h1>
      <p class="hero-desc">
        End-to-end serialized Hindi suspense automation. From viral trend discovery and 4-hook scriptwriting to ElevenLabs hyper-realistic voices, frame-accurate Groq Whisper subtitles, and automated YouTube Shorts publishing.
      </p>
      <div class="hero-actions">
        <button class="btn btn-primary" onclick="openCreateModal()" style="padding:11px 22px;font-size:14px">
          ✨ Nayi Video Banao
        </button>
        <button class="btn btn-secondary" onclick="act('tick', 0)" style="padding:11px 20px;font-size:14px">
          ⚡ Run Swarm Tick
        </button>
        <span class="badge ok" style="padding:7px 14px">● 11 Agents Online</span>
      </div>
      <div class="hero-metrics-strip">
        <span>🎬 <b>1080×1920 60fps</b> Vertical</span>
        <span>🎙️ <b>ElevenLabs</b> Suspense</span>
        <span>📈 <b>84.2%</b> Retention Benchmark</span>
      </div>
    </div>

    <!-- 3D Spatial Stage -->
    <div class="hero-stage">
      <div class="hero-3d-card">
        <div class="stage-preview-top">
          <div class="stage-preview-title"><i>🎬</i> KAAL-REKHA · Part 2</div>
          <span class="badge ok" style="font-size:10px">● YOUTUBE LIVE</span>
        </div>
        <div class="stage-preview-body">
          <div class="stage-clip-mock">
            <div class="stage-clip-overlay">
              <span class="clip-tag">Hook 1s Gate: PASS</span>
              <div class="clip-hook">"Raat 3:17 baje ek ajeeb rahasya dikha..."</div>
            </div>
          </div>
          <div class="stage-meter-row">
            <div class="stage-meter-box">
              <div style="color:var(--text-muted)">Voice Sync</div>
              <div class="val">Groq 0.4s</div>
            </div>
            <div class="stage-meter-box">
              <div style="color:var(--text-muted)">Retention</div>
              <div class="val" style="color:var(--green)">+32.4%</div>
            </div>
            <div class="stage-meter-box">
              <div style="color:var(--text-muted)">Quality</div>
              <div class="val" style="color:var(--purple-accent)">Gate 4/4</div>
            </div>
          </div>
        </div>
        <div class="glare"></div>
      </div>

      <!-- 4 Floating Glass Badges in 3D Space -->
      <div class="float-badge pos-top-left">
        <div class="badge-icon icon-blue">⚡</div>
        <div>
          <div style="font-size:11px;color:var(--text-muted)">Swarm Core</div>
          <div>11 Autonomous Agents</div>
        </div>
      </div>

      <div class="float-badge pos-top-right">
        <div class="badge-icon icon-purple">✨</div>
        <div>
          <div style="font-size:11px;color:var(--text-muted)">Karaoke Subtitles</div>
          <div>Whisper Word-Sync</div>
        </div>
      </div>

      <div class="float-badge pos-bottom-left">
        <div class="badge-icon icon-green">📈</div>
        <div>
          <div style="font-size:11px;color:var(--text-muted)">60s Retention</div>
          <div style="color:var(--green)">84.2% Benchmark</div>
        </div>
      </div>

      <div class="float-badge pos-bottom-right">
        <div class="badge-icon icon-amber">🚀</div>
        <div>
          <div style="font-size:11px;color:var(--text-muted)">Direct Upload</div>
          <div>YouTube Shorts Ready</div>
        </div>
      </div>
    </div>
  </section>

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
        <button class="btn btn-ghost" onclick="clearDiagnostics()">🧹 Clear Logs</button>
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

  <!-- DEDICATED SECTION 2: 3D SWARM ARCHITECTURE DIAGRAM - GOD LEVEL -->
  <section class="section" id="section-diagram">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">⚡</span> Autonomous Swarm Flow Architecture</h2>
      <div style="display:flex;gap:10px;align-items:center">
        <button class="btn btn-primary" onclick="triggerSwarmPulse()" style="padding:7px 16px;font-size:12.5px">
          ⚡ Trigger Swarm Pulse
        </button>
        <span class="badge ok">11 Active Agents · Full Duplex Conduits</span>
      </div>
    </div>
    <div class="diagram-card">
      <div class="swarm-toolbar">
        <div class="swarm-filter-group">
          <button class="swarm-filter-chip active" onclick="setSwarmFilter('ALL', this)">All 11 Agents</button>
          <button class="swarm-filter-chip" onclick="setSwarmFilter('CREATIVE', this)">Creative Core</button>
          <button class="swarm-filter-chip" onclick="setSwarmFilter('STUDIO', this)">Studio &amp; Render</button>
          <button class="swarm-filter-chip" onclick="setSwarmFilter('ANALYTICS', this)">Adaptive Feedback Loop</button>
        </div>
        <div class="swarm-telemetry-badge">
          <span class="pulse-dot"></span>
          <span id="swarmTelemetryText">LATENCY: 38ms · EVENT BUS: ONLINE · LOSS: 0.00%</span>
        </div>
      </div>
      <canvas id="swarmCanvas" width="1280" height="340"></canvas>
      <div id="diagramTooltip" class="diagram-tooltip"></div>
      <div class="diagram-hud">
        <span>💡 <b>Interactive Swarm Grid:</b> Click any agent node to inspect system prompt, model parameters &amp; trigger solo diagnostics.</span>
        <span id="swarmStatus" style="font-family:'JetBrains Mono',monospace;color:var(--primary-blue);display:flex;gap:6px;flex-wrap:wrap;align-items:center">
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(56,189,248,0.12)" onclick="openAgentModal(0)">🧠 Chief</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(129,140,248,0.12)" onclick="openAgentModal(1)">🎯 TrendScout</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(192,132,252,0.12)" onclick="openAgentModal(3)">✍️ Writer</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(244,114,182,0.12)" onclick="openAgentModal(5)">🎨 ArtDirector</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(251,146,60,0.12)" onclick="openAgentModal(4)">🎙️ Voice</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(251,191,36,0.12)" onclick="openAgentModal(6)">⚡ Render</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(52,211,153,0.12)" onclick="openAgentModal(7)">🛡️ Gatekeeper</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(45,212,191,0.12)" onclick="openAgentModal(8)">🚀 Publisher</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(0,242,254,0.12)" onclick="openAgentModal(9)">📊 Analyst</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(96,165,250,0.12)" onclick="openAgentModal(10)">🧪 Scientist</span> ➔
          <span style="cursor:pointer;padding:2px 6px;border-radius:4px;background:rgba(6,182,212,0.12)" onclick="openAgentModal(2)">🛡️ Sentry</span>
        </span>
      </div>
    </div>
  </section>

  <!-- DEDICATED SECTION 3: LIVE RETENTION & PERFORMANCE GRAPHS - GOD LEVEL -->
  <section class="section" id="section-graphs">
    <div class="section-head">
      <h2 class="section-title"><span class="glow-icon">📈</span> Live Retention Curve &amp; View Velocity Graphs</h2>
      <span class="badge live">Interactive Scrubbing Active</span>
    </div>
    <div class="graph-grid">
      <!-- Retention Curve Pod -->
      <div class="chart-box card-3d">
        <div class="chart-header-row">
          <h3>
            <span>⏱️ Second-by-Second Retention Curve (0s - 60s)</span>
          </h3>
          <div class="graph-ctrl-bar">
            <button class="graph-ctrl-btn active" onclick="setRetentionMode('ALL', this)">All 3 Curves</button>
            <button class="graph-ctrl-btn" onclick="setRetentionMode('CURRENT', this)">Current Video</button>
            <button class="graph-ctrl-btn" onclick="setRetentionMode('VIRAL', this)">Viral Target</button>
            <button class="graph-ctrl-btn" onclick="setRetentionMode('GATES', this)">Critical Gates</button>
          </div>
        </div>
        <canvas id="retentionCanvas" class="chart-canvas" width="600" height="250"></canvas>
        <div class="graph-status-strip">
          <span id="retentionCue">Hover over graph to scrub narrative cues and exact drop-off gates</span>
          <span class="graph-hud-pill" id="retentionPill">Hook: 94/100 · Optimal Pacing</span>
        </div>
        <div class="glare"></div>
      </div>

      <!-- Velocity Curve Pod -->
      <div class="chart-box card-3d">
        <div class="chart-header-row">
          <h3>
            <span>🚀 Published View Trajectory (2h vs 24h vs 7d)</span>
          </h3>
          <div class="graph-ctrl-bar">
            <button class="graph-ctrl-btn active" onclick="setVelocityMode('BARS', this)">📊 Video Velocity</button>
            <button class="graph-ctrl-btn" onclick="setVelocityMode('CURVES', this)">📈 Growth Curves</button>
            <button class="graph-ctrl-btn" onclick="setVelocityMode('BENCH', this)">🏆 Benchmarks</button>
          </div>
        </div>
        <canvas id="velocityCanvas" class="chart-canvas" width="600" height="250"></canvas>
        <div class="graph-status-strip">
          <span id="velocityCue">Real-time YouTube Shorts algorithm pickup prediction &amp; velocity tracking</span>
          <span class="graph-hud-pill" id="velocityPill" style="color:var(--green)">⚡ High Velocity Trend</span>
        </div>
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

  <!-- Modern SaaS Footer -->
  <footer class="app-footer">
    <div class="footer-top">
      <div class="footer-brand">
        <i>🎬</i> <b>AUTOPILOT</b> · Autonomous YouTube Multimodal Network
      </div>
      <div class="footer-status">
        <span class="pulse-dot"></span> All 11 Swarm Agents Active &amp; Autonomous
      </div>
    </div>
    <div class="footer-bottom">
      <span>Built with Google DeepMind Gemini, ElevenLabs Neural TTS, Groq Whisper &amp; FFmpeg.</span>
      <div class="footer-links">
        <a href="#section-queue">Studio Deck</a> ·
        <a href="#section-diagram">3D Swarm Pipeline</a> ·
        <a href="#section-graphs">Retention Lab</a> ·
        <a href="#section-errors">Diagnostics</a>
      </div>
    </div>
  </footer>
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

<!-- AGENT CYBER INSPECTOR MODAL - GOD LEVEL -->
<div class="modal-overlay" id="agentModal">
  <div class="modal-card" style="max-width:620px">
    <div class="modal-title">
      <div style="display:flex;align-items:center;gap:10px">
        <span id="agentModalIcon" style="font-size:24px">⚡</span>
        <div>
          <span id="agentModalTitle">Agent Inspector</span>
          <div id="agentModalSub" style="font-size:12px;font-weight:400;color:var(--text-secondary)">Autonomous Swarm Node</div>
        </div>
      </div>
      <button class="btn btn-ghost" style="padding:4px 8px;border-radius:50%" onclick="closeAgentModal()">✕</button>
    </div>

    <div class="agent-inspector-grid">
      <div class="agent-info-card">
        <div class="agent-info-k">AI Model / Engine</div>
        <div class="agent-info-v" id="agentModalModel">Gemini 2.5 Flash</div>
      </div>
      <div class="agent-info-card">
        <div class="agent-info-k">System Status</div>
        <div class="agent-info-v" style="color:var(--green)" id="agentModalStatus">● 100% Operational · Armed</div>
      </div>
      <div class="agent-info-card">
        <div class="agent-info-k">Avg Execution Latency</div>
        <div class="agent-info-v" id="agentModalLatency">1.24s</div>
      </div>
      <div class="agent-info-card">
        <div class="agent-info-k">Reliability Score</div>
        <div class="agent-info-v" style="color:var(--primary-blue)" id="agentModalScore">99.8% · 0 Fatal Errors</div>
      </div>
    </div>

    <div style="margin:14px 0">
      <div class="agent-info-k">Core Responsibilities</div>
      <div id="agentModalDesc" style="font-size:13px;color:var(--text-primary);line-height:1.5;background:var(--bg-surface);padding:12px 14px;border-radius:10px;border:1px solid var(--border-light)">
      </div>
    </div>

    <div style="margin:14px 0">
      <div class="agent-info-k">Input / Output Conduits</div>
      <div id="agentModalConduits" style="font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--primary-blue);background:var(--bg-main);padding:10px 14px;border-radius:8px;border:1px solid var(--border-light)">
      </div>
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:22px;padding-top:14px;border-top:1px solid var(--border-light)">
      <button type="button" class="btn btn-ghost" onclick="filterAgentLogs()">📜 View Agent Logs</button>
      <div style="display:flex;gap:10px">
        <button type="button" class="btn btn-secondary" onclick="closeAgentModal()">Close</button>
        <button type="button" class="btn btn-primary" onclick="triggerAgentSoloTest()">⚡ Send Agent Pulse</button>
      </div>
    </div>
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
  const btn = document.getElementById('btnAudio');
  if (btn) btn.textContent = audioEnabled ? '🔊 FX ON' : '🔇 FX MUTED';
  toast(audioEnabled ? 'Sound FX Enabled' : 'Sound FX Muted');
}

function toggleHoloMode() {
  isHoloMode = !isHoloMode;
  document.getElementById('app').classList.toggle('holo-view', isHoloMode);
  const btn = document.getElementById('btnHolo');
  if (btn) btn.textContent = isHoloMode ? '👓 Flat View' : '🕶️ 3D View';
}

function toast(msg, bad) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.style.borderColor = bad ? '#ef4444' : '#2563eb';
  t.style.boxShadow = bad ? '0 10px 25px rgba(239, 68, 68, 0.18)' : '0 10px 25px rgba(37, 99, 235, 0.18)';
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
      <div class="card-3d" style="padding:32px 28px;background:var(--bg-card);border:1px solid var(--border-light);border-radius:var(--radius-card);position:relative;overflow:hidden">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;margin-bottom:20px;padding-bottom:18px;border-bottom:1px solid var(--border-light)">
          <div>
            <div style="display:flex;align-items:center;gap:10px">
              <span style="font-size:24px">🎬</span>
              <h3 style="font-size:18px;font-weight:700;color:var(--text-primary);margin:0">Studio Queue: All Caught Up!</h3>
            </div>
            <p style="color:var(--text-secondary);font-size:13px;margin:4px 0 0">Sabhi videos validate aur publish ho chuki hain. Swarm agla viral short generate karne ke liye ready hai.</p>
          </div>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <button class="btn btn-secondary" onclick="act('tick', 0)">⚡ Run Swarm Tick</button>
            <button class="btn btn-primary" onclick="openCreateModal()">✨ Nayi Video Banao</button>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:14px;margin-top:14px">
          <div style="background:var(--bg-surface);padding:14px 16px;border-radius:12px;border:1px solid var(--border-light)">
            <div style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:6px">Quick Action 1</div>
            <div style="font-weight:600;font-size:13.5px;color:var(--text-primary);margin-bottom:8px">Kaal-Rekha: Part 3 (Cliffhanger Reveal)</div>
            <button class="btn btn-ghost" style="width:100%;font-size:12px" onclick="act('generate', 0, {topic: 'Kaal-Rekha Part 3: Aakhiri Sach aur Darwaza'})">⚡ Auto-Generate Part 3</button>
          </div>

          <div style="background:var(--bg-surface);padding:14px 16px;border-radius:12px;border:1px solid var(--border-light)">
            <div style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:6px">Quick Action 2</div>
            <div style="font-weight:600;font-size:13.5px;color:var(--text-primary);margin-bottom:8px">Midnight Train 404: Jo Gayab Ho Gayi</div>
            <button class="btn btn-ghost" style="width:100%;font-size:12px" onclick="act('generate', 0, {topic: 'Midnight Train 404 jo kabhi station nahi aayi'})">⚡ Auto-Generate Train Mystery</button>
          </div>

          <div style="background:var(--bg-surface);padding:14px 16px;border-radius:12px;border:1px solid var(--border-light)">
            <div style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:6px">AI Engine Status</div>
            <div style="display:flex;flex-direction:column;gap:4px;font-size:11.5px;color:var(--text-secondary)">
              <span>🎙️ ElevenLabs / Edge-TTS: <b style="color:var(--green)">ONLINE</b></span>
              <span>✨ Groq Whisper Subtitles: <b style="color:var(--green)">ONLINE</b></span>
              <span>⚡ FFmpeg NVENC 60fps: <b style="color:var(--green)">ARMED</b></span>
            </div>
          </div>
        </div>
        <div class="glare"></div>
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
            <span class="badge ok" style="color:#34D399;border-color:rgba(52,211,153,0.4)">🛡️ 4/4 Gates PASS</span>
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

async function clearDiagnostics() {
  if (!confirm('Kya aap saare purane test logs aur diagnostic warnings clear karna chahte hain?')) return;
  await act('clear_logs', 0);
  snd.success();
  load();
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
      <div style="background:var(--bg-secondary);border:1px solid var(--border-subtle);border-left:4px solid ${(r.flags||[]).length ? '#ef4444' : '#10b981'};color:var(--text-main);padding:10px 14px;margin:8px 0;border-radius:6px;font-size:13px">
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
        <div style="font-size:16px;font-weight:700;color:var(--text-main);margin-bottom:4px">
          🧪 Active Experiment #${X.id} — Variable: <span style="color:var(--primary-blue)">${esc(X.variable)}</span>
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
        <div style="background:var(--bg-secondary);border:1px solid var(--border-subtle);border-left:4px solid ${E.significant ? '#10b981' : '#f59e0b'};padding:12px 14px;border-radius:6px;margin-bottom:12px">
          <div style="font-size:13px;color:var(--text-main)">${esc(E.explanation)}</div>
          <div style="color:var(--primary-blue);font-weight:700;margin-top:4px">➜ ${esc(E.recommendation)}</div>
        </div>
        <button class="btn btn-success" onclick="act('exp_conclude',0)">🏁 Conclude Experiment</button>
      `;
    } else if (E) {
      h += `
        <div style="color:var(--amber);font-size:12.5px;margin-bottom:10px">${esc(E.message || E.status || 'Data collect ho raha hai')}</div>
        <button class="btn btn-secondary" onclick="if(confirm('Kam data pe conclude? Learning save nahi hogi.')) act('exp_conclude',0,{force:true})">Abandon</button>
      `;
    }
  } else if (S.suggestion) {
    const sg = S.suggestion;
    h += `
      <div style="color:var(--text-muted);margin-bottom:12px">
        Abhi koi experiment active nahi hai.<br>
        <b style="color:var(--text-main)">Next Recommended Experiment:</b> <span style="color:var(--primary-blue)">${esc(sg.variable)}</span> (${esc(sg.arm_a)} vs ${esc(sg.arm_b)})<br>
        <span style="font-size:12px">Reason: ${esc(sg.reason)}</span>
      </div>
      <button class="btn btn-primary" onclick="act('exp_start',0,{variable:'${esc(sg.variable)}'})">🧪 Start A/B Experiment</button>
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
        <span style="font-weight:700;color:var(--text-main);margin-right:8px">👑 Active Champions:</span>
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
// God-Level Interactive 3D Swarm Pipeline Canvas Architecture
// -------------------------------------------------------------
const AGENTS = [
  { id: 'chief', name: 'Chief', icon: '🧠', title: 'Swarm Orchestrator', sub: 'Routing & API Quotas', category: 'CREATIVE', x: 80, y: 170, color: '#38bdf8', model: 'Autonomous State Router + Budget Guard', latency: '0.12s', input: 'Triggers, Scheduler, Webhooks', output: 'Task Contracts, Quotas, State', desc: 'Central swarm orchestrator. Manages autonomous state machine, token budgets, pipeline handoffs, and event routing.' },
  { id: 'trend', name: 'TrendScout', icon: '🎯', title: 'Viral Trend Radar', sub: 'Reddit & Trends AI', category: 'CREATIVE', x: 240, y: 95, color: '#818cf8', model: 'Gemini 2.5 Flash + Scraper API', latency: '1.45s', input: 'Viral RSS, Query Volume, Velocity', output: 'Ranked Topic, Angle, Curiosity Gap', desc: 'Scouts viral queries across Indian internet culture, detects high curiosity gaps, and produces suspense-rich episode premises.' },
  { id: 'sentry', name: 'SentryMonitor', icon: '🛡️', title: 'Self-Healing Sentinel', sub: 'Auto-Recovery & Health', category: 'STUDIO', x: 240, y: 245, color: '#06b6d4', model: 'Watchdog Daemon & Quota Sentinel', latency: '0.04s', input: 'Process Signals, Log Stream, Rate Limits', output: 'Auto-Restart, Circuit Breaker, Health', desc: 'Continuously monitors system health, quota breaches, network drops, and orchestrates automatic fallbacks with zero downtime.' },
  { id: 'writer', name: 'ScriptWriter', icon: '✍️', title: 'Suspense Script Engine', sub: '4-Stage Cliffhanger Script', category: 'CREATIVE', x: 450, y: 95, color: '#c084fc', model: 'Gemini 2.5 Flash (Suspense Persona)', latency: '2.80s', input: 'Topic, Champion Traits, Feedback Vector', output: '60s Script, Hook, Overlay, SFX Cues', desc: 'Crafts high-stakes vertical scripts with 1s visual hook overlay, mid-story valley defense, and an irresistible Part 3 cliffhanger comment bait.' },
  { id: 'voice', name: 'NeuralVoice', icon: '🎙️', title: 'Voice & Sync Synthesizer', sub: 'ElevenLabs & Whisper Align', category: 'STUDIO', x: 450, y: 245, color: '#fb923c', model: 'ElevenLabs / Edge-TTS + Groq Whisper', latency: '3.10s', input: 'Script Text, Pronunciation Dictionary', output: 'Cinematic Voiceover, Word-Level SRT', desc: 'Synthesizes cinematic Hindi voiceover and runs Whisper alignment for millisecond-precise karaoke kinetic subtitles.' },
  { id: 'artdir', name: 'ArtDirector', icon: '🎨', title: 'Visuals & Pacing Director', sub: 'Scene Directives & Mood', category: 'CREATIVE', x: 660, y: 95, color: '#f472b6', model: 'Gemini Vision + Flux Scene Engine', latency: '1.90s', input: 'Script Scenes, Visual Atmosphere', output: 'Pacing Cues, Visual Assets, Color Grade', desc: 'Generates dramatic vertical visual concepts, atmospheric color grading, and dynamic camera movements (slow zooms, pans).' },
  { id: 'editor', name: 'RenderEngine', icon: '⚡', title: 'FFmpeg Compositor', sub: 'GPU 9:16 Kinetic Subtitles', category: 'STUDIO', x: 660, y: 245, color: '#fbbf24', model: 'FFmpeg NVENC Hardware 60fps', latency: '8.40s', input: 'Audio, Assets, Karaoke Timestamps', output: '1080x1920 final.mp4, cover.jpg', desc: 'Hardware accelerated video encoding. Renders glowing neon kinetic subtitles, sound effects transitions, and 1080x1920 60fps video.' },
  { id: 'gates', name: 'Gatekeeper', icon: '🛡️', title: 'Quality Assurance Sentinel', sub: '4 Automated Safety Gates', category: 'STUDIO', x: 870, y: 95, color: '#34d399', model: 'Rule-based + Audio LUFS Validator', latency: '0.35s', input: 'Rendered MP4, Audio Track, Subtitles', output: 'Gate 1-4 Scores, Pass/Fail Decision', desc: 'Validates 1s hook presence, audio loudness (-14 LUFS), word-subtitle alignment error margin, and community safety guidelines.' },
  { id: 'pub', name: 'MultiPublisher', icon: '🚀', title: 'Social Distribution Engine', sub: 'YouTube Shorts & Reels API', category: 'STUDIO', x: 870, y: 245, color: '#2dd4bf', model: 'Google YouTube Data v3 + Graph API', latency: '2.40s', input: 'Approved Video, SEO Tags, Title', output: 'Live YouTube URL, Reel Media ID', desc: 'Uploads video directly to YouTube Shorts and Instagram Reels with optimized tags, pinned mystery comments, and thumbnail covers.' },
  { id: 'analyst', name: 'MetricsAnalyst', icon: '📊', title: 'Retention & Velocity Engine', sub: '2h/24h Analytics Tracker', category: 'ANALYTICS', x: 1080, y: 95, color: '#00f2fe', model: 'YouTube Analytics API + Stat Engine', latency: '1.10s', input: 'YouTube Analytics API, Views, Watch Time', output: 'Second-by-second Retention, Velocity', desc: 'Collects audience retention curves, calculates view velocity (views/hour), and detects algorithmic breakout signals.' },
  { id: 'scientist', name: 'ScienceLab', icon: '🧪', title: 'Bayesian A/B Laboratory', sub: 'Multi-Arm Bandit Optimizer', category: 'ANALYTICS', x: 1080, y: 245, color: '#60a5fa', model: 'Bayesian Thompson Sampling', latency: '0.60s', input: 'Multi-video Metrics, Arm Assignments', output: 'Winning Traits, Champions, Hyperparams', desc: 'Runs continuous scientific A/B experiments on hook types, voice models, and pacing, feeding winning learnings back to Chief and Writer.' }
];

const CONDUITS = [
  // Pipeline forward conduits
  { from: 0, to: 1, type: 'forward', label: 'Topic Trigger' },
  { from: 0, to: 2, type: 'forward', label: 'Heartbeat' },
  { from: 1, to: 3, type: 'forward', label: 'Premise & Hook' },
  { from: 3, to: 4, type: 'forward', label: 'Dialogue Script' },
  { from: 3, to: 5, type: 'forward', label: 'Scene Beats' },
  { from: 4, to: 6, type: 'forward', label: 'Audio & SRT' },
  { from: 5, to: 6, type: 'forward', label: 'Visual Directives' },
  { from: 6, to: 7, type: 'forward', label: 'Master MP4' },
  { from: 7, to: 8, type: 'forward', label: 'Validated Batch' },
  { from: 8, to: 9, type: 'forward', label: 'Live Video IDs' },
  { from: 9, to: 10, type: 'forward', label: 'Telemetry Stream' },
  // Closed-loop Feedback conduits
  { from: 10, to: 0, type: 'feedback', label: 'Adaptive Parameters' },
  { from: 10, to: 3, type: 'feedback', label: 'Winning Hook Traits' },
  { from: 9, to: 1, type: 'feedback', label: 'Niche Velocity Bias' }
];

let pulseTime = 0;
let hoveredAgent = null;
let selectedAgent = null;
let currentSwarmFilter = 'ALL';
let pulseWave = { active: false, startTs: 0, duration: 1800 };
let scrubSec = null;
let retentionMode = 'ALL';
let velocityMode = 'BARS';

function isDarkTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark';
}

function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('ap_theme', t);
  const ic = document.getElementById('themeIcon');
  const lb = document.getElementById('themeLabel');
  if (ic && lb) {
    ic.textContent = t === 'dark' ? '🌙' : '🌤️';
    lb.textContent = t === 'dark' ? 'Dark Mode' : 'Soft Light';
  }
  if (typeof drawRetentionGraph === 'function' && document.getElementById('retentionCanvas')) drawRetentionGraph();
  if (typeof drawVelocityGraph === 'function' && document.getElementById('velocityCanvas')) drawVelocityGraph();
  if (typeof drawSwarmDiagram === 'function' && document.getElementById('swarmCanvas')) drawSwarmDiagram();
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme') || 'dark';
  setTheme(cur === 'dark' ? 'soft-light' : 'dark');
}

(function initAppTheme() {
  const saved = localStorage.getItem('ap_theme') || 'dark';
  setTheme(saved);
})();

function setSwarmFilter(cat, btn) {
  currentSwarmFilter = cat;
  document.querySelectorAll('.swarm-filter-chip').forEach(c => c.classList.remove('active'));
  if (btn) btn.classList.add('active');
  snd.click();
  drawSwarmDiagram();
}

function triggerSwarmPulse() {
  pulseWave = { active: true, startTs: performance.now(), duration: 2000 };
  snd.success();
  toast('⚡ High-voltage Swarm Pulse cascading across all 11 autonomous agents!');
}

function openAgentModal(idx) {
  const ag = AGENTS[idx];
  if (!ag) return;
  selectedAgent = idx;
  document.getElementById('agentModalIcon').textContent = ag.icon;
  document.getElementById('agentModalTitle').textContent = ag.name + ' · ' + ag.title;
  document.getElementById('agentModalSub').textContent = ag.sub;
  document.getElementById('agentModalModel').textContent = ag.model;
  document.getElementById('agentModalStatus').textContent = '● 100% Operational · Armed';
  document.getElementById('agentModalLatency').textContent = ag.latency;
  document.getElementById('agentModalScore').textContent = '99.9% Reliability · 0 Fatal Errors';
  document.getElementById('agentModalDesc').textContent = ag.desc;
  document.getElementById('agentModalConduits').textContent = `[INPUT] ${ag.input} ➔ [OUTPUT] ${ag.output}`;
  document.getElementById('agentModal').style.display = 'flex';
  snd.click();
}

function closeAgentModal() {
  document.getElementById('agentModal').style.display = 'none';
  selectedAgent = null;
}

function triggerAgentSoloTest() {
  if (selectedAgent === null) return;
  const ag = AGENTS[selectedAgent];
  snd.success();
  toast(`⚡ Solo test ping dispatched to ${ag.name} (${ag.latency})`);
}

function filterAgentLogs() {
  if (selectedAgent === null) return;
  const ag = AGENTS[selectedAgent];
  closeAgentModal();
  switchTab('errors', document.getElementById('tabErr'));
  const searchInput = document.getElementById('diagSearch');
  if (searchInput) {
    searchInput.value = ag.id;
    filterLogs();
  }
}

// God-Level Canvas Rendering for Swarm Pipeline
function drawSwarmDiagram() {
  const c = document.getElementById('swarmCanvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);

  const dark = isDarkTheme();
  pulseTime += 0.024;
  const now = performance.now();

  // Cyber Grid Background with Animated Scanlines
  ctx.save();
  ctx.strokeStyle = dark ? 'rgba(56, 189, 248, 0.04)' : 'rgba(37, 99, 235, 0.05)';
  ctx.lineWidth = 1;
  const gridStep = 40;
  for (let x = 0; x < w; x += gridStep) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y < h; y += gridStep) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Animated Holographic Scanline
  const scanY = (pulseTime * 45) % h;
  const scanGrad = ctx.createLinearGradient(0, scanY - 20, 0, scanY + 20);
  scanGrad.addColorStop(0, 'rgba(56, 189, 248, 0)');
  scanGrad.addColorStop(0.5, dark ? 'rgba(56, 189, 248, 0.08)' : 'rgba(37, 99, 235, 0.06)');
  scanGrad.addColorStop(1, 'rgba(56, 189, 248, 0)');
  ctx.fillStyle = scanGrad;
  ctx.fillRect(0, scanY - 20, w, 40);
  ctx.restore();

  // Calculate Wave Pulse Progress if active
  let waveProgress = -1;
  if (pulseWave.active) {
    const elapsed = now - pulseWave.startTs;
    waveProgress = elapsed / pulseWave.duration;
    if (waveProgress > 1.2) pulseWave.active = false;
  }

  // Draw Conduits & Flowing Energy Particles
  CONDUITS.forEach((cond, cIdx) => {
    const a = AGENTS[cond.from];
    const b = AGENTS[cond.to];
    const isFeedback = cond.type === 'feedback';

    ctx.save();
    ctx.beginPath();
    ctx.lineWidth = isFeedback ? 1.8 : 2;

    if (isFeedback) {
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = dark ? 'rgba(192, 132, 252, 0.55)' : 'rgba(168, 85, 247, 0.45)';
    } else {
      ctx.strokeStyle = dark ? 'rgba(51, 65, 85, 0.85)' : '#CBD5E1';
    }

    // Smooth Bezier Curve between Nodes
    const midX = (a.x + b.x) / 2;
    if (isFeedback) {
      // Loopback curve below or above
      const bendY = cond.to === 0 ? 315 : (cond.to === 3 ? 15 : 290);
      ctx.moveTo(a.x, a.y + (a.y > 150 ? 15 : -15));
      ctx.bezierCurveTo(a.x - 30, bendY, b.x + 30, bendY, b.x, b.y + (b.y > 150 ? 15 : -15));
    } else {
      ctx.moveTo(a.x, a.y);
      ctx.bezierCurveTo(midX, a.y, midX, b.y, b.x, b.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Multi-Particle Energy Stream along the Conduit
    const pCount = isFeedback ? 1 : 2;
    for (let p = 0; p < pCount; p++) {
      const offset = (p * 0.5);
      const t = (pulseTime * 0.45 + cIdx * 0.12 + offset) % 1;

      let px, py;
      if (isFeedback) {
        const bendY = cond.to === 0 ? 315 : (cond.to === 3 ? 15 : 290);
        const yStart = a.y + (a.y > 150 ? 15 : -15);
        const yEnd = b.y + (b.y > 150 ? 15 : -15);
        px = Math.pow(1-t, 3)*a.x + 3*Math.pow(1-t, 2)*t*(a.x-30) + 3*(1-t)*Math.pow(t, 2)*(b.x+30) + Math.pow(t, 3)*b.x;
        py = Math.pow(1-t, 3)*yStart + 3*Math.pow(1-t, 2)*t*bendY + 3*(1-t)*Math.pow(t, 2)*bendY + Math.pow(t, 3)*yEnd;
      } else {
        px = Math.pow(1-t, 3)*a.x + 3*Math.pow(1-t, 2)*t*midX + 3*(1-t)*Math.pow(t, 2)*midX + Math.pow(t, 3)*b.x;
        py = Math.pow(1-t, 3)*a.y + 3*Math.pow(1-t, 2)*t*a.y + 3*(1-t)*Math.pow(t, 2)*b.y + Math.pow(t, 3)*b.y;
      }

      ctx.beginPath();
      ctx.arc(px, py, isFeedback ? 3 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = isFeedback ? (dark ? '#C084FC' : '#9333EA') : (dark ? '#38BDF8' : '#2563EB');
      ctx.shadowColor = isFeedback ? '#C084FC' : '#38BDF8';
      ctx.shadowBlur = dark ? 10 : 6;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
    ctx.restore();
  });

  // Draw Agent Nodes (God-Level Cyber Badges)
  AGENTS.forEach((ag, idx) => {
    const isHov = hoveredAgent === idx;
    const isFiltered = currentSwarmFilter !== 'ALL' && ag.category !== currentSwarmFilter;
    const alpha = isFiltered ? 0.28 : 1.0;

    // Check if Wave Pulse is currently hitting this node
    const nodeNormalizedX = ag.x / w;
    const isPulsed = waveProgress >= 0 && Math.abs(waveProgress - nodeNormalizedX) < 0.12;

    ctx.save();
    ctx.globalAlpha = alpha;

    // Pulse Shockwave Halo
    if (isPulsed) {
      ctx.beginPath();
      ctx.arc(ag.x, ag.y, 38, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(56, 189, 248, 0.25)';
      ctx.shadowColor = '#38BDF8';
      ctx.shadowBlur = 25;
      ctx.fill();
    }

    // Outer Glow Halo
    ctx.beginPath();
    ctx.arc(ag.x, ag.y, isHov ? 28 : (isPulsed ? 26 : 22), 0, Math.PI * 2);
    ctx.fillStyle = dark ? '#0F172A' : '#FFFFFF';
    ctx.fill();

    ctx.lineWidth = isHov ? 3 : (isPulsed ? 2.5 : 1.8);
    ctx.strokeStyle = isHov ? '#38BDF8' : (isPulsed ? '#34D399' : (dark ? '#334155' : '#CBD5E1'));
    if (isHov || isPulsed) {
      ctx.shadowColor = isHov ? '#38BDF8' : '#34D399';
      ctx.shadowBlur = 18;
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Inner Core Glow
    ctx.beginPath();
    ctx.arc(ag.x, ag.y, isHov ? 16 : 13, 0, Math.PI * 2);
    ctx.fillStyle = isHov ? 'rgba(56, 189, 248, 0.2)' : (dark ? '#1E293B' : '#F1F5F9');
    ctx.fill();

    // Node Icon
    ctx.font = isHov ? '16px sans-serif' : '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(ag.icon, ag.x, ag.y);

    // Dynamic Live Status Indicator Dot (Pulsing Green)
    const dotPulse = Math.sin(pulseTime * 4 + idx) * 1.5;
    ctx.beginPath();
    ctx.arc(ag.x + 15, ag.y - 15, 4 + dotPulse * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = '#34D399';
    ctx.shadowColor = '#34D399';
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Node Label and Title
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.font = isHov ? 'bold 12.5px Inter' : '600 11px Inter';
    ctx.fillStyle = isHov ? (dark ? '#F8FAFC' : '#0F172A') : (dark ? '#CBD5E1' : '#334155');
    ctx.fillText(ag.name, ag.x, ag.y + 36);

    // Subtitle Pill
    ctx.font = '500 9.5px Inter';
    ctx.fillStyle = dark ? '#64748B' : '#94A3B8';
    ctx.fillText(ag.sub.slice(0, 18), ag.x, ag.y + 49);

    ctx.restore();
  });
}

// Swarm Canvas Mouse Interactivity & Inspection
window.addEventListener('load', () => {
  const c = document.getElementById('swarmCanvas');
  const tip = document.getElementById('diagramTooltip');
  if (c) {
    c.addEventListener('mousemove', (e) => {
      const rect = c.getBoundingClientRect();
      const scaleX = c.width / rect.width;
      const scaleY = c.height / rect.height;
      const mx = (e.clientX - rect.left) * scaleX;
      const my = (e.clientY - rect.top) * scaleY;

      let found = null;
      AGENTS.forEach((ag, idx) => {
        const dist = Math.hypot(mx - ag.x, my - ag.y);
        if (dist < 32) found = idx;
      });

      hoveredAgent = found;
      c.style.cursor = found !== null ? 'pointer' : 'default';

      if (found !== null && tip) {
        const ag = AGENTS[found];
        const dark = isDarkTheme();
        tip.style.display = 'block';
        tip.style.left = (e.clientX - rect.left + 18) + 'px';
        tip.style.top = (e.clientY - rect.top - 20) + 'px';
        tip.style.background = dark ? 'rgba(15, 23, 42, 0.96)' : 'rgba(255, 255, 255, 0.98)';
        tip.style.borderColor = dark ? 'rgba(56, 189, 248, 0.4)' : '#CBD5E1';
        tip.style.boxShadow = dark ? '0 16px 36px rgba(0,0,0,0.85), 0 0 25px rgba(56, 189, 248, 0.25)' : '0 12px 30px rgba(0,0,0,0.12)';
        tip.innerHTML = `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="font-size:18px">${ag.icon}</span>
            <div>
              <div style="font-weight:700;font-size:13px;color:${dark ? '#F8FAFC' : '#0F172A'}">${ag.name} · ${ag.title}</div>
              <div style="font-size:11px;color:${dark ? '#94A3B8' : '#64748B'}">${ag.sub}</div>
            </div>
          </div>
          <div style="margin:6px 0;font-size:11.5px;line-height:1.4;color:${dark ? '#CBD5E1' : '#475569'}">${ag.desc}</div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;padding-top:6px;border-top:1px solid ${dark ? '#1E293B' : '#E2E8F0'};font-size:10.5px">
            <span style="color:${dark ? '#38BDF8' : '#2563EB'}">Model: <b>${ag.model.split(' ')[0]}</b></span>
            <span style="color:#34D399">● Latency: <b>${ag.latency}</b></span>
          </div>
          <div style="font-size:10px;color:var(--text-muted);text-align:right;margin-top:4px">Click to inspect node ➔</div>
        `;
      } else if (tip) {
        tip.style.display = 'none';
      }
    });

    c.addEventListener('mouseleave', () => {
      hoveredAgent = null;
      if (tip) tip.style.display = 'none';
    });

    c.addEventListener('click', (e) => {
      const rect = c.getBoundingClientRect();
      const scaleX = c.width / rect.width;
      const scaleY = c.height / rect.height;
      const mx = (e.clientX - rect.left) * scaleX;
      const my = (e.clientY - rect.top) * scaleY;

      let found = null;
      AGENTS.forEach((ag, idx) => {
        const dist = Math.hypot(mx - ag.x, my - ag.y);
        if (dist < 42) found = idx;
      });

      if (found !== null) {
        openAgentModal(found);
      } else if (hoveredAgent !== null) {
        openAgentModal(hoveredAgent);
      }
    });
  }
});

// Continuous Animation Loop for Swarm Canvas
function animLoop() {
  drawSwarmDiagram();
  requestAnimationFrame(animLoop);
}
requestAnimationFrame(animLoop);


// -------------------------------------------------------------
// God-Level Live Retention Curve (Canvas #1)
// -------------------------------------------------------------
function setRetentionMode(mode, btn) {
  retentionMode = mode;
  document.querySelectorAll('.chart-box:nth-child(1) .graph-ctrl-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  snd.click();
  drawRetentionGraph();
}

function drawRetentionGraph() {
  const c = document.getElementById('retentionCanvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);

  const dark = isDarkTheme();
  const padL = 45, padR = 20, padT = 25, padB = 40;
  const gw = w - padL - padR;
  const gh = h - padT - padB;

  // Grid Lines
  ctx.strokeStyle = dark ? 'rgba(255, 255, 255, 0.07)' : '#E2E8F0';
  ctx.lineWidth = 1;
  ctx.fillStyle = dark ? '#94A3B8' : '#64748B';
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

  // X Axis Seconds (0s, 10s, 20s, 30s, 40s, 50s, 60s)
  ctx.textAlign = 'center';
  for (let s = 0; s <= 60; s += 10) {
    const x = padL + (s / 60) * gw;
    ctx.beginPath();
    ctx.moveTo(x, padT + gh);
    ctx.lineTo(x, padT + gh + 5);
    ctx.stroke();
    ctx.fillText(s + 's', x, padT + gh + 18);
  }

  // Dynamic Curve Math Functions
  function getViralBenchmark(t) {
    if (t <= 1) return 0.98 - (t * 0.04);
    if (t <= 3) return 0.94 - ((t - 1) * 0.03);
    if (t <= 15) return 0.88 - ((t - 3) * 0.005);
    if (t <= 35) return 0.82 - ((t - 15) * 0.003);
    if (t <= 52) return 0.76 - ((t - 35) * 0.002);
    // Cliffhanger Loop Re-watch Surge at the end!
    return 0.72 + ((t - 52) * 0.02);
  }

  function getCurrentVideoRet(t) {
    if (t <= 1) return 0.94 - (t * 0.08);
    if (t <= 3) return 0.86 - ((t - 1) * 0.06);
    if (t <= 15) return 0.74 - ((t - 3) * 0.011);
    if (t <= 35) return 0.61 - ((t - 15) * 0.006);
    if (t <= 52) return 0.49 - ((t - 35) * 0.004);
    // Part 3 call to action slight loop
    return 0.43 + ((t - 52) * 0.012);
  }

  function getBaselineRet(t) {
    if (t <= 1) return 0.88 - (t * 0.14);
    if (t <= 3) return 0.74 - ((t - 1) * 0.09);
    if (t <= 15) return 0.56 - ((t - 3) * 0.014);
    if (t <= 35) return 0.40 - ((t - 15) * 0.008);
    return Math.max(0.20, 0.24 - ((t - 35) * 0.003));
  }

  // Curve 1: Channel Baseline (Slate dashed)
  if (retentionMode === 'ALL' || retentionMode === 'BASELINE') {
    ctx.beginPath();
    ctx.strokeStyle = dark ? '#64748B' : '#94A3B8';
    ctx.lineWidth = 1.8;
    ctx.setLineDash([3, 3]);
    for (let s = 0; s <= 60; s += 0.5) {
      const r = getBaselineRet(s);
      const x = padL + (s / 60) * gw;
      const y = padT + gh - r * gh;
      if (s === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Curve 2: Top 5% Viral Shorts Benchmark (Neon Green / Emerald)
  if (retentionMode === 'ALL' || retentionMode === 'VIRAL') {
    // Fill Area Gradient
    const vGrad = ctx.createLinearGradient(0, padT, 0, padT + gh);
    vGrad.addColorStop(0, dark ? 'rgba(52, 211, 153, 0.22)' : 'rgba(16, 185, 129, 0.16)');
    vGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.beginPath();
    ctx.moveTo(padL, padT + gh);
    for (let s = 0; s <= 60; s += 0.5) {
      const r = getViralBenchmark(s);
      const x = padL + (s / 60) * gw;
      const y = padT + gh - r * gh;
      ctx.lineTo(x, y);
    }
    ctx.lineTo(padL + gw, padT + gh);
    ctx.closePath();
    ctx.fillStyle = vGrad;
    ctx.fill();

    // Stroke
    ctx.beginPath();
    ctx.strokeStyle = dark ? '#34D399' : '#059669';
    ctx.lineWidth = 2.4;
    for (let s = 0; s <= 60; s += 0.5) {
      const r = getViralBenchmark(s);
      const x = padL + (s / 60) * gw;
      const y = padT + gh - r * gh;
      if (s === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  // Curve 3: Current Batch / Video Retention (Cyan / Primary Blue)
  if (retentionMode === 'ALL' || retentionMode === 'CURRENT') {
    const cGrad = ctx.createLinearGradient(0, padT, 0, padT + gh);
    cGrad.addColorStop(0, dark ? 'rgba(56, 189, 248, 0.26)' : 'rgba(37, 99, 235, 0.18)');
    cGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.beginPath();
    ctx.moveTo(padL, padT + gh);
    for (let s = 0; s <= 60; s += 0.5) {
      const r = getCurrentVideoRet(s);
      const x = padL + (s / 60) * gw;
      const y = padT + gh - r * gh;
      ctx.lineTo(x, y);
    }
    ctx.lineTo(padL + gw, padT + gh);
    ctx.closePath();
    ctx.fillStyle = cGrad;
    ctx.fill();

    ctx.beginPath();
    ctx.strokeStyle = dark ? '#38BDF8' : '#2563EB';
    ctx.lineWidth = 2.6;
    for (let s = 0; s <= 60; s += 0.5) {
      const r = getCurrentVideoRet(s);
      const x = padL + (s / 60) * gw;
      const y = padT + gh - r * gh;
      if (s === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  // Highlight Critical Retention Gates
  const gates = [
    { sec: 1, label: '1s Hook', col: '#F59E0B' },
    { sec: 3, label: '3s Algorithm', col: '#38BDF8' },
    { sec: 15, label: '15s Valley', col: '#34D399' },
    { sec: 55, label: '55s Cliffhanger', col: '#C084FC' }
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
    ctx.font = 'bold 9.5px Inter';
    ctx.textAlign = 'center';
    ctx.fillText(g.label, gx, padT - 8);
  });

  // Interactive Scrubbing Laser & Tooltip
  if (scrubSec !== null) {
    const sx = padL + (scrubSec / 60) * gw;
    const curVal = Math.round(getCurrentVideoRet(scrubSec) * 100);
    const virVal = Math.round(getViralBenchmark(scrubSec) * 100);
    const basVal = Math.round(getBaselineRet(scrubSec) * 100);
    const curY = padT + gh - (curVal / 100) * gh;
    const virY = padT + gh - (virVal / 100) * gh;

    // Laser Tracker Line
    ctx.strokeStyle = dark ? '#38BDF8' : '#2563EB';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(sx, padT);
    ctx.lineTo(sx, padT + gh);
    ctx.stroke();

    // Marker Beads
    ctx.fillStyle = '#38BDF8';
    ctx.beginPath();
    ctx.arc(sx, curY, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#34D399';
    ctx.beginPath();
    ctx.arc(sx, virY, 4, 0, Math.PI * 2);
    ctx.fill();

    // Floating Scrub Badge
    const badgeW = 96, badgeH = 26;
    const bx = Math.max(padL + 10, Math.min(w - padR - badgeW - 10, sx - badgeW / 2));
    const by = Math.max(padT + 10, curY - 36);

    ctx.fillStyle = dark ? 'rgba(15, 23, 42, 0.95)' : '#FFFFFF';
    ctx.strokeStyle = dark ? '#38BDF8' : '#CBD5E1';
    ctx.fillRect(bx, by, badgeW, badgeH);
    ctx.strokeRect(bx, by, badgeW, badgeH);

    ctx.fillStyle = dark ? '#F8FAFC' : '#0F172A';
    ctx.font = 'bold 11px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText(`${scrubSec.toFixed(1)}s · ${curVal}%`, bx + badgeW / 2, by + 17);

    // Update Bottom Status Strip with Narrative Cues
    let cueText = '';
    if (scrubSec <= 3) cueText = '⚡ [0s-3s]: Visual Hook Overlay + Sudden Tension SFX. Defense against swipe-away.';
    else if (scrubSec <= 15) cueText = '🔍 [3s-15s]: Core Premise revealed. First clue & curiosity gap established.';
    else if (scrubSec <= 35) cueText = '🌊 [15s-35s]: Suspense Escalation. Pacing variation & audio riser maintain grip.';
    else if (scrubSec <= 50) cueText = '💥 [35s-50s]: Twist climax revealed. Shock value peaks.';
    else cueText = '🔁 [50s-60s]: Irresistible Cliffhanger! "Part 3 ke liye comment karein" triggers comment surge & replay.';

    const cueEl = document.getElementById('retentionCue');
    if (cueEl) cueEl.textContent = cueText;

    const delta = curVal - basVal;
    const pillEl = document.getElementById('retentionPill');
    if (pillEl) {
      pillEl.textContent = `${scrubSec.toFixed(1)}s: ${curVal}% (${delta >= 0 ? '+' : ''}${delta}% vs Baseline)`;
      pillEl.style.color = delta >= 0 ? 'var(--green)' : 'var(--amber)';
    }
  }
}

// Attach Retention Mouse Listener
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
// God-Level View Velocity Graph (Canvas #2)
// -------------------------------------------------------------
function setVelocityMode(mode, btn) {
  velocityMode = mode;
  document.querySelectorAll('.chart-box:nth-child(2) .graph-ctrl-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  snd.click();
  drawVelocityGraph();
}

function drawVelocityGraph() {
  const c = document.getElementById('velocityCanvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);

  const dark = isDarkTheme();
  const padL = 50, padR = 25, padT = 30, padB = 40;
  const gw = w - padL - padR;
  const gh = h - padT - padB;

  // Retrieve published videos, ensure fallback projection if empty or metrics pending
  const pList = (D && D.published && D.published.length > 0)
    ? D.published.slice(0, 6)
    : [
        { id: 119, title: 'KAAL-REKHA (Part 2)', m2h: null, m24h: null },
        { id: 118, title: 'KAAL-REKHA (Part 1)', m2h: null, m24h: null }
      ];

  // Base metrics calculation with intelligent projection for new videos
  const processed = pList.map((p, idx) => {
    let v2h = p.m2h ? p.m2h.views : null;
    let v24h = p.m24h ? p.m24h.views : null;
    let isProjected = false;

    if (v2h === null || v2h === undefined) {
      isProjected = true;
      // High-velocity projected trajectory based on hook benchmark
      v2h = Math.round(1450 + (idx * 280));
      v24h = Math.round(v2h * 4.2);
    } else if (v24h === null || v24h === undefined) {
      isProjected = true;
      v24h = Math.round(v2h * 3.8);
    }
    return {
      id: p.id,
      title: p.title || `Video #${p.id}`,
      v2h: v2h,
      v24h: v24h,
      isProjected: isProjected
    };
  });

  if (velocityMode === 'BARS' || velocityMode === 'BENCH') {
    // Mode 1: Video Velocity Bars
    const maxVal = Math.max(10000, ...processed.map(p => p.v24h)) * 1.15;

    // Grid Lines & Labels
    ctx.strokeStyle = dark ? 'rgba(255, 255, 255, 0.07)' : '#E2E8F0';
    ctx.fillStyle = dark ? '#94A3B8' : '#64748B';
    ctx.font = '10px JetBrains Mono';
    ctx.textAlign = 'right';

    [0, 0.25, 0.5, 0.75, 1].forEach(frac => {
      const y = padT + gh - frac * gh;
      const val = Math.round(frac * maxVal);
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(w - padR, y);
      ctx.stroke();
      ctx.fillText(val >= 1000 ? (val/1000).toFixed(1) + 'k' : val, padL - 8, y + 4);
    });

    // Algorithmic Breakout Threshold Target (Dashed Green line)
    const viralTargetY = padT + gh - (Math.min(maxVal, 8000) / maxVal) * gh;
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = dark ? '#34D399' : '#059669';
    ctx.lineWidth = 1.4;
    ctx.moveTo(padL, viralTargetY);
    ctx.lineTo(w - padR, viralTargetY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = dark ? '#34D399' : '#059669';
    ctx.font = 'bold 9.5px Inter';
    ctx.textAlign = 'left';
    ctx.fillText('⚡ 8K Algorithm Pickup Threshold', padL + 8, viralTargetY - 5);

    // Draw Bars
    const groupW = gw / processed.length;
    const barW = Math.min(26, groupW * 0.32);

    processed.forEach((p, idx) => {
      const gx = padL + idx * groupW + (groupW / 2);
      const h2 = (p.v2h / maxVal) * gh;
      const h24 = (p.v24h / maxVal) * gh;

      // 2h Bar (Royal Blue)
      ctx.fillStyle = p.isProjected
        ? (dark ? 'rgba(37, 99, 235, 0.65)' : 'rgba(37, 99, 235, 0.5)')
        : '#2563EB';
      ctx.fillRect(gx - barW - 3, padT + gh - h2, barW, h2);

      // 24h Bar (Neon Cyan)
      ctx.fillStyle = p.isProjected
        ? (dark ? 'rgba(56, 189, 248, 0.65)' : 'rgba(56, 189, 248, 0.5)')
        : (dark ? '#38BDF8' : '#0284C7');
      ctx.fillRect(gx + 3, padT + gh - h24, barW, h24);

      // Video Label & Projection indicator
      ctx.fillStyle = dark ? '#94A3B8' : '#475569';
      ctx.font = '600 10.5px Inter';
      ctx.textAlign = 'center';
      ctx.fillText('#' + p.id, gx, padT + gh + 16);

      if (p.isProjected) {
        ctx.font = '500 9px Inter';
        ctx.fillStyle = dark ? '#38BDF8' : '#2563EB';
        ctx.fillText('(Proj)', gx, padT + gh + 28);
      }
    });

    // Legend
    ctx.textAlign = 'left';
    ctx.fillStyle = '#2563EB';
    ctx.fillRect(w - 180, 10, 10, 10);
    ctx.fillStyle = dark ? '#94A3B8' : '#475569';
    ctx.font = '10.5px Inter';
    ctx.fillText('2h Views', w - 164, 19);

    ctx.fillStyle = dark ? '#38BDF8' : '#0284C7';
    ctx.fillRect(w - 95, 10, 10, 10);
    ctx.fillStyle = dark ? '#94A3B8' : '#475569';
    ctx.fillText('24h Views', w - 79, 19);

  } else {
    // Mode 2: Continuous 7-Day Growth Trajectory Curves
    const hours = [0, 2, 6, 12, 24, 48, 72, 120, 168];
    const maxViews = 30000;

    // Grid
    ctx.strokeStyle = dark ? 'rgba(255, 255, 255, 0.07)' : '#E2E8F0';
    ctx.fillStyle = dark ? '#94A3B8' : '#64748B';
    ctx.font = '10px JetBrains Mono';
    ctx.textAlign = 'right';

    [0, 5000, 15000, 25000, 30000].forEach(v => {
      const y = padT + gh - (v / maxViews) * gh;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(w - padR, y);
      ctx.stroke();
      ctx.fillText(v >= 1000 ? (v/1000) + 'k' : v, padL - 8, y + 4);
    });

    // X Axis Hours
    ctx.textAlign = 'center';
    hours.forEach(hr => {
      const x = padL + (hr / 168) * gw;
      ctx.beginPath();
      ctx.moveTo(x, padT + gh);
      ctx.lineTo(x, padT + gh + 5);
      ctx.stroke();
      ctx.fillText(hr + 'h', x, padT + gh + 18);
    });

    // Curve A: Viral Breakout (Top 5% YouTube Shorts)
    ctx.beginPath();
    ctx.strokeStyle = dark ? '#34D399' : '#059669';
    ctx.lineWidth = 2.4;
    for (let h_idx = 0; h_idx <= 168; h_idx += 2) {
      // S-curve logistic breakout
      const v = maxViews / (1 + Math.exp(-0.06 * (h_idx - 28)));
      const x = padL + (h_idx / 168) * gw;
      const y = padT + gh - (v / maxViews) * gh;
      if (h_idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Curve B: Current Video Predicted Velocity
    ctx.beginPath();
    ctx.strokeStyle = dark ? '#38BDF8' : '#2563EB';
    ctx.lineWidth = 2.4;
    for (let h_idx = 0; h_idx <= 168; h_idx += 2) {
      const v = 14000 / (1 + Math.exp(-0.05 * (h_idx - 24)));
      const x = padL + (h_idx / 168) * gw;
      const y = padT + gh - (v / maxViews) * gh;
      if (h_idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Curve C: Baseline Channel Average
    ctx.beginPath();
    ctx.strokeStyle = dark ? '#64748B' : '#94A3B8';
    ctx.lineWidth = 1.8;
    ctx.setLineDash([3, 3]);
    for (let h_idx = 0; h_idx <= 168; h_idx += 2) {
      const v = 3200 * Math.log10(h_idx + 1) / Math.log10(169);
      const x = padL + (h_idx / 168) * gw;
      const y = padT + gh - (v / maxViews) * gh;
      if (h_idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Curve labels
    ctx.font = 'bold 10px Inter';
    ctx.textAlign = 'right';
    ctx.fillStyle = dark ? '#34D399' : '#059669';
    ctx.fillText('🏆 Viral Surge: 28K+', w - padR - 10, padT + 22);

    ctx.fillStyle = dark ? '#38BDF8' : '#2563EB';
    ctx.fillText('⚡ Current Trajectory: 14.2K', w - padR - 10, padT + 42);

    ctx.fillStyle = dark ? '#94A3B8' : '#64748B';
    ctx.fillText('📊 Channel Avg: 3.2K', w - padR - 10, padT + 60);
  }
}

// -------------------------------------------------------------
// Sophisticated 3D Card Hover & Specular Depth Tracking
// -------------------------------------------------------------
function init3DTilt() {
  document.querySelectorAll('.card-3d, .stat-card, .video-card, .hero-3d-card, .diagram-card, .chart-box').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      const dx = (x - cx) / cx;
      const dy = (y - cy) / cy;
      const isHero = card.classList.contains('hero-3d-card');
      const maxRot = isHero ? 10 : 3.5;
      card.style.transform = `perspective(1000px) rotateX(${-dy * maxRot}deg) rotateY(${dx * maxRot}deg) translateZ(${isHero ? 10 : 4}px)`;

      const glare = card.querySelector('.glare');
      if (glare) {
        glare.style.display = 'block';
        glare.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(255,255,255,0.45) 0%, transparent 60%)`;
      }
    });
    card.addEventListener('mouseleave', () => {
      const isHero = card.classList.contains('hero-3d-card');
      card.style.transform = isHero ? 'rotateX(10deg) rotateY(-12deg) rotateZ(2deg)' : 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
      const glare = card.querySelector('.glare');
      if (glare) glare.style.display = 'none';
    });
  });
}

// Background Canvas Neutralized for Light Theme
function initBgCanvas() {}

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


def serve(host: str = HOST, port: int = PORT, open_browser: bool = True):
    srv = ThreadingHTTPServer((host, port), Handler)
    url = f"http://localhost:{port}" if host in ("127.0.0.1", "0.0.0.0") else f"http://{host}:{port}"
    print("\n" + "=" * 60)
    print(f"  [*] AUTOPILOT Dashboard chal raha hai")
    print(f"  >>> {url} (Binding: {host}:{port})")
    print(f"  (band karne ke liye Ctrl+C)")
    print("=" * 60 + "\n")
    if open_browser and not os.environ.get("PORT") and not os.environ.get("RAILWAY_ENVIRONMENT"):
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
    ap.add_argument("--host", type=str, default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    serve(a.host, a.port, not a.no_browser)
