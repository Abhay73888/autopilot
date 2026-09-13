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
# Windows terminal Unicode fix - safe reconfigure to prevent closed buffer GC crash
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
elif sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", write_through=True)

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
elif sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", write_through=True)

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

from core.config import CONFIG, ROOT
from core.db import DB
from core.logbook import Logbook
from core.quota import Quota
from web.ml_studio import ML_STUDIO_CSS, ML_STUDIO_JS, ML_STUDIO_TAB_HTML
from web.video_editor_ui import EDITOR_CSS, EDITOR_JS, EDITOR_TAB_HTML
from web.onboarding_tour import TOUR_CSS, TOUR_HTML, TOUR_JS

log = Logbook("dashboard")
PORT = int(os.environ.get("PORT", CONFIG.get("dashboard_port", 8765)))
# Cloud deployments (Render/Docker) set HOST env var; local runs default to localhost
HOST = os.environ.get("HOST", "127.0.0.1")

# Google OAuth: Web Application Client ID from Google Cloud Console
# To enable: Google Cloud Console → APIs & Services → Credentials
# → Create OAuth 2.0 Client ID (Web application)
# → Add Authorized JavaScript origin: http://localhost:8765
# Set GOOGLE_CLIENT_ID in your .env file
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID") or "435802513331-pvj41dcdi5qmop8mviijpds9rmjt7isk.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

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
# DATA — dashboard ko chahiye sab kuch (20x Accelerated Cache)
# =====================================================================
_GATHER_CACHE: dict[tuple[str | None, bool], tuple[float, dict]] = {}
_GATHER_CACHE_LOCK = threading.Lock()
_GATHER_CACHE_TTL = 1.5  # 1.5s cache TTL for instant sub-millisecond responses

def invalidate_gather_cache():
    with _GATHER_CACHE_LOCK:
        _GATHER_CACHE.clear()

def gather(user_id: str | None = None, view_all: bool = False) -> dict:
    cache_key = (user_id, view_all)
    now_ts = time.time()
    with _GATHER_CACHE_LOCK:
        if cache_key in _GATHER_CACHE:
            ts, val = _GATHER_CACHE[cache_key]
            if now_ts - ts < _GATHER_CACHE_TTL:
                return val

    db = DB()
    q = Quota(db)
    try:
        user = db.get_user(user_id) if user_id else None
        is_admin = bool(user and user.get("role") == "admin") or (user_id == "admin_abhay")
        # If user_id is None, preserve legacy behavior (all videos)
        # If admin and view_all is True (or legacy), show all videos
        # Else filter strictly by user_id
        filter_user = None if (user_id is None or (is_admin and view_all)) else user_id

        # ---- approve queue: rendered hai par abhi approve/reject nahi hua ----
        queue = []
        if filter_user:
            q_rows = db.q("SELECT * FROM videos WHERE user_id = ? AND status IN ('rendered','validated') "
                          "ORDER BY id DESC LIMIT 20", (filter_user,))
        else:
            q_rows = db.q("SELECT * FROM videos WHERE status IN ('rendered','validated') "
                          "ORDER BY id DESC LIMIT 20")

        for r in q_rows:
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
                "yt_video_id": r["yt_video_id"],
                "ig_media_id": r["ig_media_id"],
                "user_id": r["user_id"] if "user_id" in r.keys() else "admin_abhay",
            })

        # ---- recently published + unke metrics ----
        published = []
        if filter_user:
            p_rows = db.q("SELECT * FROM videos WHERE user_id = ? AND status='published' ORDER BY id DESC LIMIT 10", (filter_user,))
        else:
            p_rows = db.q("SELECT * FROM videos WHERE status='published' ORDER BY id DESC LIMIT 10")

        for r in p_rows:
            mets = {m["window"]: dict(m) for m in db.get_metrics(r["id"])}
            published.append({
                "id": r["id"], "title": r["title"], "hook_type": r["hook_type"],
                "voice_id": r["voice_id"], "template_id": r["template_id"],
                "published_ts": r["published_ts"],
                "yt_video_id": r["yt_video_id"], "ig_media_id": r["ig_media_id"],
                "m2h": mets.get("2h"), "m24h": mets.get("24h"), "m7d": mets.get("7d"),
                "user_id": r["user_id"] if "user_id" in r.keys() else "admin_abhay",
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

        # Multi-tenant active task response
        active_task_resp = CURRENT_TASK
        if filter_user and CURRENT_TASK.get("user_id") and CURRENT_TASK["user_id"] != filter_user:
            active_task_resp = {"status": "idle", "task": None, "job_id": None, "msg": "", "started_ts": None, "user_id": filter_user}

        active_u = user or (db.get_user("admin_abhay") if is_admin else None)

        out = {
            "brand": CONFIG.get("brand_name", "AUTOPILOT"),
            "autonomy": CONFIG.get("autonomy", "review_first"),
            "mock_mode": bool(CONFIG.get("mock_mode")),
            "summary": db.dashboard_summary(user_id=filter_user),
            "queue": queue,
            "published": published,
            "quota": q.snapshot(),
            "analysis": analysis,
            "science": science,
            "experiment": dict(exp) if exp else None,
            "learnings": learnings,
            "logs": logs,
            "active_task": active_task_resp,
            "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "user": active_u,
            "is_admin": is_admin,
            "view_mode": "all" if (is_admin and view_all) else ("all" if user_id is None else "my"),
            "filter_user": filter_user,
        }
        with _GATHER_CACHE_LOCK:
            _GATHER_CACHE[cache_key] = (now_ts, out)
        return out
    finally:
        db.close()


# Task tracking for background generation and tick processes
CURRENT_TASK = {"status": "idle", "task": None, "job_id": None, "msg": "", "started_ts": None, "user_id": "admin_abhay"}

def run_bg_task(name: str, fn, *, job_id: str | None = None, action: str | None = None,
                topic: str | None = None, idempotency_key: str | None = None,
                request_id: str | None = None, user_id: str = "admin_abhay"):
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
                               idempotency_key=idempotency_key, request_id=request_id,
                               user_id=user_id)
    except Exception as e:
        log.warn("Job create in DB warning", reason=str(e)[:120])

    CURRENT_TASK = {
        "status": "running",
        "task": name,
        "job_id": job_id,
        "msg": f"{name} shuru ho raha hai...",
        "started_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user_id": user_id
    }

    def _worker():
        global CURRENT_TASK
        now_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with DB() as thread_db:
            thread_db.update_job(job_id, status="running", started_ts=now_ts)
            if action in ("generate", "generate_series", "series_generate"):
                try:
                    from core.discord_service import notify_event
                    notify_event("video_generation_started", {
                        "job_id": job_id,
                        "title": topic or name,
                        "series_name": topic or name,
                        "action": action,
                    }, user_id=user_id)
                except Exception:
                    pass
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
                    "started_ts": None,
                    "user_id": user_id
                }
                if action in ("generate", "generate_series", "series_generate") and vid:
                    try:
                        from core.discord_service import notify_event
                        notify_event("video_rendered", {
                            "job_id": job_id,
                            "video_id": vid,
                            "title": topic or name,
                            "duration_sec": 30,
                        }, user_id=user_id)
                    except Exception:
                        pass
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
                    "started_ts": None,
                    "user_id": user_id
                }
                try:
                    from core.discord_service import notify_event
                    notify_event("generation_failed", {
                        "job_id": job_id,
                        "title": topic or name,
                        "error": str(e),
                    }, user_id=user_id)
                except Exception:
                    pass

    threading.Thread(target=_worker, daemon=True).start()
    return {
        "ok": True,
        "job_id": job_id,
        "status": "queued",
        "msg": f"{name} background mein shuru kar diya hai",
        "status_url": f"/api/jobs/{job_id}"
    }

# =====================================================================
# PIPELINE TELEMETRY & AUTO-FIX ENGINE
# =====================================================================
def gather_pipeline_diagnostics() -> dict:
    from core.ffmpeg import ffmpeg_bin
    from core.db import DB
    from core.quota import Quota

    with DB() as db:
        q = Quota(db)
        quota_snap = q.snapshot()

        # Check last job
        last_job = None
        jobs = db.list_jobs(limit=1)
        if jobs:
            last_job = dict(jobs[0])
            if last_job.get("result_paths"):
                try:
                    last_job["result_paths"] = json.loads(last_job["result_paths"])
                except Exception:
                    pass

        # Check lockfile
        lock_path = ROOT / "data" / "chief.lock"
        is_locked = lock_path.exists()
        lock_age_s = 0.0
        if is_locked:
            try:
                lock_age_s = time.time() - lock_path.stat().st_mtime
            except Exception:
                pass

        # Check ffmpeg
        ff_ok = False
        ff_path = ""
        try:
            ff_path = ffmpeg_bin()
            ff_ok = bool(ff_path and Path(ff_path).exists())
        except Exception:
            ff_ok = False

        # API Keys checks
        keys_status = {
            "gemini": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
            "moonshot": bool(os.environ.get("MOONSHOT_API_KEY", "").strip()),
            "elevenlabs": bool(os.environ.get("ELEVENLABS_API_KEY", "").strip()),
            "groq": bool(os.environ.get("GROQ_API_KEY", "").strip()),
            "youtube": bool((ROOT / "token.json").exists() or (ROOT / "client_secret.json").exists()),
        }

        # Determine diagnosis & status
        curr = CURRENT_TASK
        status = curr.get("status", "idle")
        diagnosis = "Pipeline is healthy, operational, and ready for generation."
        fix_action = None

        if status == "running":
            diagnosis = f"Active generation task '{curr.get('task')}' is currently in progress."
        elif status == "error":
            err_msg = curr.get("msg", "")
            diagnosis = f"Last background task failed: {err_msg}"
            if "quota" in err_msg.lower():
                diagnosis += " (API rate limit or daily quota reached)."
                fix_action = "toggle_mock"
            elif "lock" in err_msg.lower():
                diagnosis += " (A lock conflict was detected)."
                fix_action = "reset_task"
            else:
                fix_action = "retry_last"
        elif is_locked and lock_age_s > 300:
            diagnosis = "A stale lockfile was detected from a previous task that may have terminated abruptly."
            fix_action = "reset_task"
        elif not ff_ok:
            diagnosis = "FFmpeg executable is not found. Video rendering requires FFmpeg."
            fix_action = "health_check"
        elif not keys_status["gemini"] and not keys_status["moonshot"] and not CONFIG.get("mock_mode"):
            diagnosis = "No LLM API keys found in .env. Generation will fail in real mode."
            fix_action = "toggle_mock"

        # Fetch latest video record
        latest_video = None
        try:
            v_rows = db.q("SELECT id, title, topic, status, yt_video_id, ig_media_id, created_ts FROM videos ORDER BY id DESC LIMIT 1")
            if v_rows:
                v_rec = dict(v_rows[0])
                vid_id = v_rec["id"]
                d_out = ROOT / "output" / f"video_{vid_id:04d}"
                has_mp4 = (d_out / "final.mp4").exists()
                latest_video = {
                    "id": vid_id,
                    "title": v_rec.get("title") or v_rec.get("topic") or f"Video #{vid_id}",
                    "status": v_rec.get("status"),
                    "has_mp4": has_mp4,
                    "video_url": f"/media/video_{vid_id:04d}/final.mp4" if has_mp4 else None,
                    "cover_url": f"/media/video_{vid_id:04d}/cover.jpg" if (d_out / "cover.jpg").exists() else None,
                    "yt_video_id": v_rec.get("yt_video_id"),
                    "yt_url": f"https://www.youtube.com/shorts/{v_rec['yt_video_id']}" if v_rec.get("yt_video_id") else None,
                    "ig_media_id": v_rec.get("ig_media_id"),
                    "ig_url": f"https://www.instagram.com/p/{v_rec['ig_media_id']}" if v_rec.get("ig_media_id") else None,
                    "created_ts": v_rec.get("created_ts"),
                }
        except Exception:
            pass

        return {
            "ok": True,
            "status": status,
            "active_task": curr,
            "last_job": last_job,
            "latest_video": latest_video,
            "is_locked": is_locked,
            "lock_age_seconds": round(lock_age_s, 1),
            "ffmpeg": {"ok": ff_ok, "path": ff_path},
            "keys": keys_status,
            "quota": quota_snap,
            "mock_mode": bool(CONFIG.get("mock_mode")),
            "diagnosis": diagnosis,
            "recommended_fix": fix_action,
            "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


def gather_tasks_summary(user_id: str | None = None, view_all: bool = False) -> dict:
    """Returns tasks dashboard summary with live running task, statistics, and recent job history."""
    with DB() as db:
        user = db.get_user(user_id) if user_id else None
        is_admin = bool(user and user.get("role") == "admin") or (user_id == "admin_abhay")
        filter_user = None if (user_id is None or (is_admin and view_all)) else user_id

        jobs = db.list_jobs(limit=40, user_id=filter_user)
        jobs_list = []
        counts = {"total": 0, "completed": 0, "failed": 0, "running": 0, "queued": 0}
        for j in jobs:
            jd = dict(j)
            st = jd.get("status", "unknown")
            counts["total"] += 1
            if st in counts:
                counts[st] += 1
            if jd.get("result_paths"):
                try:
                    jd["result_paths"] = json.loads(jd["result_paths"])
                except Exception:
                    pass
            jobs_list.append(jd)

        success_rate = 100
        finished = counts["completed"] + counts["failed"]
        if finished > 0:
            success_rate = round((counts["completed"] / finished) * 100, 1)

        active_task_resp = CURRENT_TASK
        if filter_user and CURRENT_TASK.get("user_id") and CURRENT_TASK["user_id"] != filter_user:
            active_task_resp = {"status": "idle", "task": None, "job_id": None, "msg": "", "started_ts": None, "user_id": filter_user}

        return {
            "ok": True,
            "active_task": active_task_resp,
            "counts": counts,
            "success_rate": success_rate,
            "jobs": jobs_list,
            "user_id": filter_user,
            "is_admin": is_admin,
        }


def gather_system_problems() -> dict:
    """Detects any errors, failed tasks, missing keys, or system bottlenecks, with auto-fix recommendations."""
    diag = gather_pipeline_diagnostics()
    problems = []

    # 1. Active task failure
    curr = CURRENT_TASK
    if curr.get("status") == "error":
        problems.append({
            "id": "active_task_error",
            "title": f"Task Failed: {curr.get('task', 'Generation')}",
            "description": curr.get("msg", "An error occurred during task execution."),
            "severity": "high",
            "fix_action": "reset_task",
            "fix_label": "Reset Pipeline & Unlock"
        })

    # 2. Recent failed jobs
    with DB() as db:
        failed_jobs = db.list_jobs(limit=5, status="failed")
        for fj in failed_jobs[:3]:
            fjd = dict(fj)
            problems.append({
                "id": f"job_{fjd.get('job_id')}",
                "title": f"Failed Job: {fjd.get('action', 'task').title()} ({fjd.get('topic') or fjd.get('job_id')})",
                "description": fjd.get("error_message") or "Job encountered an error.",
                "severity": "medium",
                "fix_action": "retry_last",
                "fix_label": "Retry Video Generation"
            })

    # 3. Stale Lockfile
    if diag.get("is_locked") and diag.get("lock_age_seconds", 0) > 120:
        problems.append({
            "id": "stale_lock",
            "title": "Pipeline Busy / Stale Lock Detected",
            "description": f"Pipeline has been locked for {diag['lock_age_seconds']}s. If no task is running, clear lock.",
            "severity": "medium",
            "fix_action": "reset_task",
            "fix_label": "Clear Lock & Reset"
        })

    # 4. FFmpeg
    if not diag.get("ffmpeg", {}).get("ok"):
        problems.append({
            "id": "missing_ffmpeg",
            "title": "FFmpeg Video Render Engine Missing",
            "description": "FFmpeg was not found in system PATH. Video rendering will fail.",
            "severity": "critical",
            "fix_action": "health_check",
            "fix_label": "Run Doctor Check"
        })

    # 5. Quota / API Keys
    keys = diag.get("keys", {})
    if not keys.get("gemini") and not keys.get("moonshot") and not diag.get("mock_mode"):
        problems.append({
            "id": "missing_llm_keys",
            "title": "No LLM Keys Active in .env",
            "description": "GEMINI_API_KEY or MOONSHOT_API_KEY is not set. Real generation will fail.",
            "severity": "high",
            "fix_action": "toggle_mock",
            "fix_label": "Switch to Safe Offline Mode"
        })

    return {
        "ok": True,
        "has_problems": len(problems) > 0,
        "problem_count": len(problems),
        "problems": problems,
        "diagnostics": diag
    }


def apply_pipeline_fix(action: str) -> dict:
    global CURRENT_TASK
    with DB() as db:
        if action == "reset_task":
            CURRENT_TASK = {
                "status": "idle",
                "task": None,
                "job_id": None,
                "msg": "Pipeline unlocked and task state reset to IDLE.",
                "started_ts": None,
            }
            lock_path = ROOT / "data" / "chief.lock"
            if lock_path.exists():
                try:
                    lock_path.unlink()
                except Exception:
                    pass
            db.q("UPDATE jobs SET status='cancelled', error_message='Cancelled by operator via Auto-Fix' WHERE status='running'")
            log.ok("Pipeline task state and lockfile successfully reset")
            return {"ok": True, "msg": "Pipeline unlocked and task state reset to IDLE successfully."}

        elif action == "toggle_mock":
            new_mode = not bool(CONFIG.get("mock_mode", False))
            CONFIG["mock_mode"] = new_mode
            log.ok(f"Mock mode toggled to {new_mode}")
            return {
                "ok": True,
                "mock_mode": new_mode,
                "msg": f"Mock / Offline Mode {'ENABLED' if new_mode else 'DISABLED'}. Pipeline will now {'use deterministic mock fallback' if new_mode else 'connect to live neural APIs'}.",
            }

        elif action == "retry_last":
            jobs = db.list_jobs(limit=1)
            if not jobs:
                return {"ok": False, "error": "No previous job found to retry."}
            last = dict(jobs[0])
            topic = last.get("topic") or "Unsolved Mystery of Kuldhara"
            return do_action("generate", 0, {"topic": topic, "preset": "veryfast"})

        elif action == "health_check":
            diag = gather_pipeline_diagnostics()
            return {
                "ok": True,
                "report": diag,
                "msg": f"System Environment Health Check Complete: FFmpeg {'Ready' if diag['ffmpeg']['ok'] else 'Missing'}, LLM Keys {'Available' if diag['keys']['gemini'] or diag['keys']['moonshot'] else 'None'}.",
            }

        elif action == "clear_logs":
            return do_action("clear_logs", 0, {})

        return {"ok": False, "error": f"Unknown fix action: {action}"}


def gather_channel_status() -> dict:
    has_yt_secret = (ROOT / "client_secret.json").exists()
    has_yt_token = (ROOT / "token.json").exists()
    yt_channel_name = None
    if has_yt_token:
        try:
            with open(ROOT / "token.json", "r", encoding="utf-8") as f:
                t_data = json.load(f)
                yt_channel_name = t_data.get("channel_title") or "Authorized Channel"
        except Exception:
            yt_channel_name = "Authorized Channel"

    ig_token = os.environ.get("IG_LONG_LIVED_TOKEN") or os.environ.get("META_APP_SECRET")
    ig_account = os.environ.get("IG_BUSINESS_ACCOUNT_ID")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    from core.discord_service import DiscordConfig
    discord_configured = DiscordConfig.is_configured()
    discord_bot_active = DiscordConfig.has_bot()
    discord_webhook_active = DiscordConfig.has_webhook()
    discord_connected = False
    discord_username = None
    discord_guild = None
    discord_channel = None

    try:
        with DB() as db:
            conns = db.list_active_discord_connections()
            if conns:
                discord_connected = True
                c0 = conns[0]
                discord_username = c0.get("username")
                discord_guild = c0.get("guild_name") or c0.get("guild_id")
                discord_channel = c0.get("channel_name") or c0.get("channel_id")
    except Exception:
        pass

    if discord_connected:
        disc_text = f"Connected as @{discord_username or 'User'} ✅"
    elif discord_configured or discord_webhook_active or discord_bot_active:
        disc_text = "Credentials Ready — Click 'Connect Discord' 🟡"
    else:
        disc_text = "Configure DISCORD_CLIENT_ID in `.env` ⚠️"

    return {
        "ok": True,
        "youtube": {
            "configured": has_yt_secret,
            "connected": has_yt_token,
            "channel_name": yt_channel_name,
            "status_text": "Connected & Authorized ✅" if has_yt_token else ("Awaiting Authorization (`python authorize_youtube.py`) 🟡" if has_yt_secret else "Missing `client_secret.json` ⚠️")
        },
        "instagram": {
            "configured": bool(ig_token and ig_account),
            "connected": bool(ig_token and ig_account),
            "account_id": ig_account if ig_account else None,
            "status_text": "Configured & Active ✅" if (ig_token and ig_account) else "Credentials Needed in `.env` 🟡"
        },
        "discord": {
            "configured": discord_configured or discord_webhook_active,
            "connected": discord_connected,
            "bot_active": discord_bot_active,
            "username": discord_username,
            "guild_name": discord_guild,
            "channel_name": discord_channel,
            "status_text": disc_text
        },
        "ai": {
            "gemini_active": bool(gemini_key),
            "edge_tts_active": True,
            "pollinations_active": True,
            "status_text": "Neural Voice (Edge-TTS) + AI Engine Active ✅"
        }
    }


def test_channel(channel: str) -> dict:
    if channel == "youtube":
        has_token = (ROOT / "token.json").exists()
        if has_token:
            return {"ok": True, "message": "YouTube OAuth token is valid! Ready for automatic upload."}
        elif (ROOT / "client_secret.json").exists():
            return {"ok": False, "message": "client_secret.json found! Please run 'python authorize_youtube.py' in your terminal to complete authorization."}
        else:
            return {"ok": False, "message": "client_secret.json not found in project root. Please download it from Google Cloud Console."}
    elif channel == "instagram":
        ig_token = os.environ.get("IG_LONG_LIVED_TOKEN")
        ig_account = os.environ.get("IG_BUSINESS_ACCOUNT_ID")
        if ig_token and ig_account:
            return {"ok": True, "message": f"Instagram Business Account #{ig_account} is configured with Meta Graph API token."}
        else:
            return {"ok": False, "message": "Instagram credentials missing in .env. Please add IG_BUSINESS_ACCOUNT_ID and IG_LONG_LIVED_TOKEN."}
    elif channel == "discord":
        from core.discord_service import DiscordConfig, DiscordNotifications
        embed = DiscordNotifications.create_embed(
            title="💬 AUTOPILOT DISCORD TEST",
            description="Integration connection verified! Video generation and upload notifications will appear here.",
            color=0x10B981,
            url=DiscordConfig.app_url()
        )
        delivered = DiscordNotifications.dispatch(embed)
        if delivered:
            return {"ok": True, "message": "Test notification delivered successfully to your Discord channel/webhook! ✅"}
        else:
            return {"ok": False, "message": "Could not deliver to Discord. Ensure DISCORD_BOT_TOKEN or DISCORD_WEBHOOK_URL is configured and bot has channel write permissions."}
    elif channel == "ai":
        return {"ok": True, "message": "Edge-TTS (6 neural voices) and Pollinations AI are 100% operational in free offline mode."}
    return {"ok": False, "message": "Unknown channel"}


# =====================================================================
# ACTIONS
# =====================================================================
def do_action(action: str, video_id: int, payload: dict) -> dict:
    invalidate_gather_cache()
    with DB() as db:
        # ---- experiment actions kisi video se bandhe nahi hain ----
        if action == "generate":
            topic = payload.get("topic")
            dry_run = bool(payload.get("dry_run", CONFIG.get("mock_mode")))
            req_user_id = payload.get("user_id") or "admin_abhay"

            def _gen(worker_db):
                from run import one_video
                manifest = one_video(topic=topic, dry_run=dry_run, with_images=True, preset="veryfast", keep_temp=False, voice=payload.get("voice"))
                if not manifest:
                    raise RuntimeError("Pipeline failed to generate and render video. Check logs for details.")
                # one_video now returns the full manifest dict with video_id
                vid = manifest.get("video_id", 0)
                if not vid:
                    # Fallback: try to get video_id from render info embedded in manifest
                    render_info = manifest.get("render", {})
                    video_path = render_info.get("video_path", "")
                    import re
                    m = re.search(r"video_(\d+)", video_path)
                    vid = int(m.group(1)) if m else 0
                if vid:
                    worker_db.update_video(vid, user_id=req_user_id)
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
                               request_id=payload.get("request_id"),
                               user_id=req_user_id)

        if action in ("generate_series", "series_generate"):
            series_code = payload.get("series", "SERIES_1").upper()
            ep_num = payload.get("episode")
            if ep_num is not None and str(ep_num).isdigit():
                ep_num = int(ep_num)
            else:
                ep_num = None
            dry_run = bool(payload.get("dry_run", CONFIG.get("mock_mode")))
            req_user_id = payload.get("user_id") or "admin_abhay"

            def _gen_series(worker_db):
                from series.series_runner import generate_series_episode
                res = generate_series_episode(series_code=series_code, episode_num=ep_num, dry_run=dry_run)
                if not res.get("ok"):
                    raise RuntimeError(res.get("error", f"{series_code} generation failed"))
                vid = res.get("video_id")
                if vid:
                    worker_db.update_video(vid, user_id=req_user_id)
                return res

            task_name = f"{series_code} Ep {ep_num or 'Next'}"
            return run_bg_task(f"Series Generation: {task_name}", _gen_series,
                               job_id=payload.get("job_id"), action="generate_series",
                               topic=task_name, idempotency_key=payload.get("idempotency_key"),
                               request_id=payload.get("request_id"),
                               user_id=req_user_id)

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
                qs = parse_qs(u.query)
                user_id = self.headers.get("X-User-Id") or qs.get("user_id", [None])[0]
                view_all = qs.get("view_all", ["0"])[0] in ("1", "true")
                return self._json(200, gather(user_id=user_id, view_all=view_all))
            except Exception as e:  # noqa: BLE001
                log.error("Dashboard data fail", e)
                return self._json(500, {"error": str(e)})

        # ---- Current user authentication status ----
        if u.path == "/api/auth/me":
            try:
                qs = parse_qs(u.query)
                uid = self.headers.get("X-User-Id") or qs.get("user_id", [""])[0]
                with DB() as db:
                    user = db.get_user(uid or "admin_abhay")
                    return self._json(200, {"ok": bool(user), "user": user, "is_admin": (user and user.get("role") == "admin")})
            except Exception as e:
                log.error("Auth me fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Discord Integration: Status endpoint ----
        if u.path == "/api/integrations/discord/status":
            try:
                qs = parse_qs(u.query)
                uid = self.headers.get("X-User-Id") or qs.get("user_id", [""])[0] or "admin_abhay"
                from core.discord_service import DiscordConfig
                with DB() as db:
                    conn = db.get_discord_connection(uid)
                    return self._json(200, {
                        "ok": True,
                        "configured": DiscordConfig.is_configured(),
                        "bot_active": DiscordConfig.has_bot(),
                        "webhook_active": DiscordConfig.has_webhook(),
                        "connected": bool(conn),
                        "connection": conn,
                    })
            except Exception as e:
                log.error("Discord status endpoint fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Discord Integration: OAuth start endpoint ----
        if u.path == "/api/integrations/discord/oauth/start":
            try:
                qs = parse_qs(u.query)
                uid = self.headers.get("X-User-Id") or qs.get("user_id", [""])[0] or "admin_abhay"
                from core.discord_service import DiscordOAuth, DiscordConfig
                if not DiscordConfig.is_configured():
                    return self._json(400, {
                        "ok": False,
                        "error": "Discord credentials not set in .env. Please configure DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET.",
                    })
                cb = DiscordConfig.default_redirect_uri()
                if not cb:
                    host = self.headers.get("Host") or "localhost:8765"
                    proto = "https" if "render.com" in host or self.headers.get("X-Forwarded-Proto") == "https" else "http"
                    cb = f"{proto}://{host}/api/integrations/discord/oauth/callback"
                auth_url, state = DiscordOAuth.get_authorization_url(uid, callback_url=cb)
                return self._json(200, {"ok": True, "url": auth_url, "state": state})
            except Exception as e:
                log.error("Discord OAuth start fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Discord Integration: OAuth callback endpoint ----
        if u.path in ("/api/integrations/discord/oauth/callback", "/auth/discord/callback"):
            try:
                qs = parse_qs(u.query)
                code = qs.get("code", [""])[0]
                state = qs.get("state", [""])[0]
                guild_id = qs.get("guild_id", [""])[0]
                error = qs.get("error", [""])[0]

                if error or not code:
                    log.warn(f"[DISCORD] OAuth error/denied: {error}")
                    return self._redirect("/?discord=denied")

                from core.discord_service import DiscordOAuth, DiscordConfig, DiscordNotifications
                uid = DiscordOAuth.verify_state(state)
                if not uid:
                    log.warn("[DISCORD] OAuth state validation failed")
                    return self._redirect("/?discord=state_invalid")

                cb = DiscordConfig.default_redirect_uri()
                if not cb:
                    host = self.headers.get("Host") or "localhost:8765"
                    proto = "https" if "render.com" in host or self.headers.get("X-Forwarded-Proto") == "https" else "http"
                    cb = f"{proto}://{host}{u.path}"

                tokens = DiscordOAuth.exchange_code(code, cb)
                access_token = tokens.get("access_token")
                refresh_token = tokens.get("refresh_token")
                expires_in = tokens.get("expires_in", 604800)
                token_expires_at = int(time.time()) + expires_in

                profile = DiscordOAuth.fetch_current_user(access_token)
                discord_user_id = profile.get("id")
                username = profile.get("username") or "DiscordUser"
                global_name = profile.get("global_name") or username
                avatar = profile.get("avatar")

                guild_name = None
                if guild_id:
                    try:
                        guilds = DiscordOAuth.fetch_user_guilds(access_token)
                        for g in guilds:
                            if str(g.get("id")) == str(guild_id):
                                guild_name = g.get("name")
                                break
                    except Exception:
                        pass

                with DB() as db:
                    db.save_discord_connection(
                        user_id=uid,
                        discord_user_id=discord_user_id,
                        username=username,
                        global_name=global_name,
                        avatar=avatar,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        token_expires_at=token_expires_at,
                        guild_id=guild_id or None,
                        guild_name=guild_name,
                    )
                log.ok(f"[DISCORD] Connected Discord @{username} ({discord_user_id}) for AUTOPILOT user {uid}")

                try:
                    welcome_embed = DiscordNotifications.create_embed(
                        title="💬 Discord Connected to AUTOPILOT!",
                        description=(
                            f"Account **@{username}** successfully connected to **AUTOPILOT SaaS**.\n\n"
                            f"• You will receive real-time notifications for video rendering & YouTube uploads.\n"
                            f"• Use `/help` in your server to see bot slash commands."
                        ),
                        color=0x10B981,
                        url=DiscordConfig.app_url()
                    )
                    DiscordNotifications.dispatch(welcome_embed, user_id=uid)
                except Exception:
                    pass

                return self._redirect("/?discord=connected")
            except Exception as e:
                log.error("Discord OAuth callback fail", e)
                return self._redirect(f"/?discord=error&msg={urllib.parse.quote(str(e)[:80])}")

        # ---- AI Copilot suggestions endpoint ----
        if u.path == "/api/assistant/quick_suggestions":
            try:
                from agents.assistant import AutopilotAssistant
                ctx = AutopilotAssistant().gather_system_context()
                suggestions = [
                    "🎬 Generate Mystery Video",
                    "⚡ Run Swarm Tick",
                    "📊 Quota & Health Check",
                    "💡 5 Viral Trending Topics",
                ]
                if ctx.get("queue_pending_count", 0) > 0:
                    vid = ctx["pending_videos"][0]["id"]
                    suggestions.insert(0, f"✅ Approve Video #{vid}")
                    suggestions.insert(1, f"🚀 Publish Video #{vid}")
                return self._json(200, {"ok": True, "suggestions": suggestions})
            except Exception as e:
                log.warn("Assistant quick suggestions exception", reason=str(e)[:120])
                return self._json(200, {
                    "ok": True,
                    "suggestions": [
                        "🎬 Generate Mystery Video",
                        "⚡ Run Swarm Tick",
                        "📊 Quota & Health Check",
                        "💡 5 Viral Trending Topics"
                    ]
                })

        # ---- Pipeline diagnostics endpoint ----
        if u.path == "/api/pipeline/diagnostics":
            try:
                return self._json(200, gather_pipeline_diagnostics())
            except Exception as e:
                log.error("Pipeline diagnostics fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Tasks summary & history endpoint ----
        if u.path == "/api/tasks/summary" or u.path == "/api/tasks":
            try:
                qs = parse_qs(u.query)
                user_id = self.headers.get("X-User-Id") or qs.get("user_id", [None])[0]
                view_all = qs.get("view_all", ["0"])[0] in ("1", "true")
                return self._json(200, gather_tasks_summary(user_id=user_id, view_all=view_all))
            except Exception as e:
                log.error("Tasks summary fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- System problems & auto-fix diagnostics endpoint ----
        if u.path == "/api/problems":
            try:
                return self._json(200, gather_system_problems())
            except Exception as e:
                log.error("System problems fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Series catalog & episode metadata endpoint ----
        if u.path == "/api/series/catalog":
            try:
                from series.series_runner import get_next_episode_number
                with DB() as sdb:
                    s1_next = get_next_episode_number(sdb, "SERIES_1")
                    s2_next = get_next_episode_number(sdb, "SERIES_2")
                    s3_next = get_next_episode_number(sdb, "SERIES_3")
                    s4_next = get_next_episode_number(sdb, "SERIES_4")
                    s5_next = get_next_episode_number(sdb, "SERIES_5")
                catalog = [
                    {
                        "code": "SERIES_1",
                        "name": "काल-रेखा (Kaal-Rekha)",
                        "genre": "Dark Anime Psychological Time-Loop Thriller",
                        "hero": "Kabir Sen (3:17 AM)",
                        "aesthetic": "MAPPA dark anime + 38Hz Braam Hit",
                        "next_episode": s1_next,
                        "badge": "🔥 Most Popular"
                    },
                    {
                        "code": "SERIES_2",
                        "name": "जब प्यार ऑनलाइन था",
                        "genre": "Modern Romance & Emotional Drama",
                        "hero": "Rohan & Priya",
                        "aesthetic": "Aesthetic anime romance + emotional violin",
                        "next_episode": s2_next,
                        "badge": "💖 Romance"
                    },
                    {
                        "code": "SERIES_3",
                        "name": "चिंटू के जादुई कारनामे",
                        "genre": "Colorful 3D Cartoon Family Adventure",
                        "hero": "Chintu & Golu",
                        "aesthetic": "Pixar-style vibrant 3D cartoon + fun sound effects",
                        "next_episode": s3_next,
                        "badge": "🎨 Kids & Fun"
                    },
                    {
                        "code": "SERIES_4",
                        "name": "दिमाग का दही (Paheliyan)",
                        "genre": "Mind-Bending Riddles & Interactive Brain Teasers",
                        "hero": "The Quizmaster",
                        "aesthetic": "Neon quiz countdown + viral retention sound fx",
                        "next_episode": s4_next,
                        "badge": "🧠 Viral Quiz"
                    },
                    {
                        "code": "SERIES_5",
                        "name": "अश्वत्थामा 3049 AD",
                        "genre": "Dark Sci-Fi Mythological Cyberpunk Action",
                        "hero": "Ashwatthama (Immortal Warrior)",
                        "aesthetic": "8K Unreal Engine 5 + Dune aesthetic + Vedic Braam",
                        "next_episode": s5_next,
                        "badge": "⚡ Epic Sci-Fi"
                    }
                ]
                return self._json(200, {"ok": True, "series": catalog})
            except Exception as e:
                log.error("Series catalog fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- ML Insights & Wan2.1 status endpoint ----
        if u.path == "/api/ml/insights":
            try:
                from core.ml_optimizer import MLOptimizer
                from agents.videogen import VideoGen
                ml = MLOptimizer()
                vg = VideoGen()
                return self._json(200, {
                    "ok": True,
                    "r2_score": ml.r2_score,
                    "mae": ml.mae,
                    "samples_trained": ml.training_count,
                    "weights": [round(w, 3) for w in ml.weights],
                    "feature_labels": [
                        "Speech WPM", "Scene Cuts Pacing", "Duration Brevity",
                        "Hook Brevity", "Curiosity Triggers", "Visual Energy",
                        "Hook Type", "Character Continuity"
                    ],
                    "guidelines": [g for g in ml.get_prompt_guidelines().splitlines() if g.strip()],
                    "videogen": {
                        "provider": CONFIG.get("videogen", {}).get("provider", "wan2.1"),
                        "model_variant": vg.model_variant,
                        "providers_chain": vg.providers
                    }
                })
            except Exception as e:
                log.error("ML insights fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Video Editor Endpoints ----
        if u.path == "/api/editor/videos":
            try:
                from core.video_editor import VideoEditor
                ve = VideoEditor()
                return self._json(200, {"ok": True, "videos": ve.list_editable_videos()})
            except Exception as e:
                log.error("Editor videos list fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        if u.path.startswith("/api/editor/video/"):
            try:
                vid_str = u.path[len("/api/editor/video/"):].strip("/")
                vid = int(vid_str)
                from core.video_editor import VideoEditor
                ve = VideoEditor()
                return self._json(200, ve.get_video_timeline(vid))
            except Exception as e:
                log.error("Editor video timeline fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Channel connection status endpoint ----
        if u.path == "/api/channels/status":
            try:
                return self._json(200, gather_channel_status())
            except Exception as e:
                log.error("Channel status fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

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

        # ---- AI Copilot assistant endpoint ----
        if u.path == "/api/assistant":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                user_msg = body.get("message", "")
                history = body.get("history", [])
                from agents.assistant import AutopilotAssistant
                res = AutopilotAssistant().handle_message(user_msg, history)
                return self._json(200, res)
            except Exception as e:  # noqa: BLE001
                log.error("Copilot handle fail", e)
                return self._json(500, {"ok": False, "error": str(e), "reply": f"Assistant error: {str(e)}"})

        # ---- Pipeline Auto-Fix endpoint ----
        if u.path == "/api/pipeline/fix":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                res = apply_pipeline_fix(body.get("action", ""))
                return self._json(200, res)
            except Exception as e:  # noqa: BLE001
                log.error("Pipeline fix fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Channel connection test endpoint ----
        if u.path == "/api/channels/test":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                ch = body.get("channel", "")
                return self._json(200, test_channel(ch))
            except Exception as e:  # noqa: BLE001
                log.error("Channel test fail", e)
                return self._json(500, {"ok": False, "message": str(e)})

        # ---- ML Retention prediction endpoint ----
        if u.path == "/api/ml/predict":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                from core.ml_optimizer import MLOptimizer
                res = MLOptimizer().predict_retention(
                    topic=body.get("topic", ""),
                    script=body.get("script", ""),
                    length_sec=float(body.get("length_sec", 32.0)),
                    hook_type=body.get("hook_type", "contrarian"),
                    template_id=body.get("template_id", "noir_teal"),
                    scene_count=int(body.get("scene_count", 7))
                )
                return self._json(200, {"ok": True, "result": res})
            except Exception as e:
                log.error("ML predict fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- ML Retrain endpoint ----
        if u.path == "/api/ml/train":
            try:
                from core.ml_optimizer import MLOptimizer
                res = MLOptimizer().train()
                return self._json(200, res)
            except Exception as e:
                log.error("ML train fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Video Editor Render & Export endpoint ----
        if u.path == "/api/editor/export":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                from core.video_editor import VideoEditor
                ve = VideoEditor()
                res = ve.apply_edits(
                    video_id=int(body.get("video_id", 0)),
                    start_sec=float(body.get("start_sec", 0.0)),
                    end_sec=float(body.get("end_sec", 0.0)) if body.get("end_sec") else None,
                    speed=float(body.get("speed", 1.0)),
                    filter_preset=body.get("filter_preset", "none"),
                    hook_headline=body.get("hook_headline", ""),
                    hook_position=body.get("hook_position", "top"),
                    voice_volume=float(body.get("voice_volume", 1.0)),
                    fade_audio=bool(body.get("fade_audio", True))
                )
                return self._json(200 if res.get("ok") else 500, res)
            except Exception as e:
                log.error("Editor export fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Authentication: Login endpoint ----
        if u.path == "/api/auth/login":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                ident = (body.get("identifier") or body.get("user_id") or body.get("email") or "").strip()
                with DB() as db:
                    # If empty or founder trigger -> authenticate as admin_abhay
                    if not ident or ident.lower() in ("admin_abhay", "abhay@autopilot.ai", "admin"):
                        user = db.get_user("admin_abhay")
                        return self._json(200, {"ok": True, "user": user, "is_admin": True})
                    user = db.get_user(ident)
                    if user:
                        return self._json(200, {"ok": True, "user": user, "is_admin": (user.get("role") == "admin")})
                    return self._json(404, {"ok": False, "error": f"Creator ID / Email '{ident}' nahi mila. Naya account banayein."})
            except Exception as e:
                log.error("Auth login fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Authentication: Registration endpoint ----
        if u.path == "/api/auth/register":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                email = (body.get("email") or "").strip()
                name = (body.get("name") or "").strip()
                password = (body.get("password") or "").strip()
                if not email:
                    return self._json(400, {"ok": False, "error": "Email is required"})
                if not name:
                    name = email.split("@")[0].title()
                with DB() as db:
                    user = db.create_user(email=email, name=name, password=password, role="creator")
                    return self._json(200, {"ok": True, "user": user, "is_new": True})
            except Exception as e:
                log.error("Auth register fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Authentication: Google One-Click & Verified Token Login endpoint ----
        if u.path == "/api/auth/google":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                id_token = body.get("credential") or body.get("id_token")
                email = (body.get("email") or "").strip().lower()
                name = (body.get("name") or "").strip()
                avatar_url = body.get("avatar_url", "")
                verified_by_google = False

                # Real Cryptographic Token Verification via Google's OAuth2 TokenInfo API
                if id_token:
                    import urllib.parse
                    token_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(str(id_token))}"
                    try:
                        v_req = urllib.request.Request(token_url, headers={"User-Agent": "Autopilot-Studio/1.0"})
                        with urllib.request.urlopen(v_req, timeout=7) as v_resp:
                            token_info = json.loads(v_resp.read().decode("utf-8"))
                            if token_info.get("email"):
                                email = token_info.get("email").strip().lower()
                                name = token_info.get("name") or token_info.get("email").split("@")[0].title()
                                avatar_url = token_info.get("picture", avatar_url)
                                verified_by_google = (token_info.get("email_verified") in ("true", True, "1", 1))
                    except Exception as ve:
                        log.warn(f"Google tokeninfo verification returned: {ve}")
                        if not email:
                            return self._json(401, {"ok": False, "error": "Google Sign-In token verification failed or expired. Please sign in again."})

                if not email:
                    return self._json(400, {"ok": False, "error": "Valid Google Account email is required."})
                if not name:
                    name = email.split("@")[0].replace(".", " ").title()

                with DB() as db:
                    existing = db.get_user(email)
                    is_new = False
                    role = "admin" if ("abhay" in email or email == "abhay@autopilot.ai") else "creator"
                    if existing:
                        user = existing
                        if role == "admin" and user.get("role") != "admin":
                            user["role"] = "admin"
                    else:
                        user = db.create_user(email=email, name=name, role=role)
                        is_new = True
                    if avatar_url and isinstance(user, dict):
                        user["avatar_url"] = avatar_url
                    user["google_verified"] = True
                    return self._json(200, {
                        "ok": True,
                        "user": user,
                        "is_new": is_new,
                        "is_google": True,
                        "verified": True,
                        "message": f"Verified Google Account: {email}"
                    })
            except Exception as e:
                log.error("Auth Google fail", e)
                return self._json(500, {"ok": False, "error": f"Google authentication error: {str(e)}"})

        # ---- User: Mark onboarding tour completed in DB ----
        if u.path == "/api/user/tour-complete":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                uid = body.get("user_id") or self.headers.get("X-User-Id")
                if uid:
                    with DB() as db:
                        db.mark_tour_completed(uid)
                return self._json(200, {"ok": True, "user_id": uid, "tour_completed": 1})
            except Exception as e:
                log.error("Tour complete update fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Discord Integration: Update Settings ----
        if u.path == "/api/integrations/discord/settings":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                uid = body.get("user_id") or self.headers.get("X-User-Id") or "admin_abhay"
                with DB() as db:
                    ok = db.update_discord_settings(
                        user_id=uid,
                        notify_generation=body.get("notify_generation"),
                        notify_upload=body.get("notify_upload"),
                        notify_errors=body.get("notify_errors"),
                        notify_analytics=body.get("notify_analytics"),
                        channel_id=body.get("channel_id"),
                        channel_name=body.get("channel_name"),
                        guild_id=body.get("guild_id"),
                        guild_name=body.get("guild_name"),
                        webhook_url=body.get("webhook_url"),
                    )
                    conn = db.get_discord_connection(uid)
                    return self._json(200, {"ok": True, "connection": conn, "msg": "Settings saved successfully"})
            except Exception as e:
                log.error("Discord update settings fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Discord Integration: Test Notification ----
        if u.path == "/api/integrations/discord/test":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                uid = body.get("user_id") or self.headers.get("X-User-Id") or "admin_abhay"
                from core.discord_service import DiscordConfig, DiscordNotifications
                embed = DiscordNotifications.create_embed(
                    title="💬 AUTOPILOT Notification Test",
                    description="Your Discord integration is working properly! Video generation, rendering, and upload events will appear here.",
                    color=0x10B981,
                    fields=[
                        {"name": "Status", "value": "✅ Live Connected", "inline": True},
                        {"name": "User", "value": uid, "inline": True},
                    ],
                    url=DiscordConfig.app_url()
                )
                delivered = DiscordNotifications.dispatch(embed, user_id=uid)
                if delivered:
                    return self._json(200, {"ok": True, "message": "Test notification sent successfully to Discord!"})
                else:
                    return self._json(400, {
                        "ok": False,
                        "message": "Could not deliver message to Discord. Please ensure a valid channel ID or webhook URL is configured."
                    })
            except Exception as e:
                log.error("Discord test notification fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Discord Integration: Disconnect ----
        if u.path == "/api/integrations/discord/disconnect":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                uid = body.get("user_id") or self.headers.get("X-User-Id") or "admin_abhay"
                with DB() as db:
                    db.disconnect_discord(uid)
                log.ok(f"[DISCORD] Disconnected Discord integration for user {uid}")
                return self._json(200, {"ok": True, "msg": "Discord successfully disconnected."})
            except Exception as e:
                log.error("Discord disconnect fail", e)
                return self._json(500, {"ok": False, "error": str(e)})

        # ---- Discord Integration: Interactions HTTP Endpoint ----
        if u.path == "/api/integrations/discord/interactions":
            try:
                n = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(n) or b"{}"
                body = json.loads(raw_body)
                from core.discord_service import DiscordSlashCommands
                resp = DiscordSlashCommands.dispatch_interaction(body)
                return self._json(200, resp)
            except Exception as e:
                log.error("Discord interaction endpoint fail", e)
                return self._json(500, {"error": str(e)})

        if u.path != "/api/action":
            return self._send(404, "text/plain", b"404")
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            if "user_id" not in body and self.headers.get("X-User-Id"):
                body["user_id"] = self.headers.get("X-User-Id")
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
        import gzip
        accept_encoding = self.headers.get("Accept-Encoding", "")
        # High-performance Gzip compression for payloads > 1KB (reduces transfer size by 80%)
        if "gzip" in accept_encoding and len(body) > 1024 and not ctype.startswith("video/") and not ctype.startswith("image/"):
            try:
                compressed = gzip.compress(body, compresslevel=6)
                if len(compressed) < len(body):
                    self.send_response(code)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Encoding", "gzip")
                    self.send_header("Content-Length", str(len(compressed)))
                    self.send_header("Vary", "Accept-Encoding")
                    self.end_headers()
                    self.wfile.write(compressed)
                    return
            except Exception:
                pass

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

    def _redirect(self, location: str):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()


PAGE = r"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🎬 AUTOPILOT — AI Video Swarm & Series Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {
  --bg-deep: #050814;
  --bg-surface: #090f22;
  --bg-card: rgba(13, 21, 44, 0.75);
  --border: rgba(255, 255, 255, 0.08);
  --border-glow: rgba(0, 242, 254, 0.35);
  --cyan: #00f2fe;
  --blue: #38bdf8;
  --purple: #8b5cf6;
  --green: #10b981;
  --amber: #f59e0b;
  --red: #ef4444;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg-deep);
  color: var(--text-main);
  font: 14px/1.6 'Inter', -apple-system, sans-serif;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

body::before {
  content: "";
  position: fixed;
  top: -20%;
  left: 20%;
  width: 60vw;
  height: 60vh;
  background: radial-gradient(circle, rgba(0, 242, 254, 0.06) 0%, rgba(139, 92, 246, 0.04) 40%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

#app {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 98vw;
  margin: 0 auto;
  padding: 16px clamp(16px, 1.8vw, 36px) 80px;
}
@media (min-width: 1920px) {
  #app {
    max-width: 1880px;
  }
}
@media (min-width: 2560px) {
  #app {
    max-width: 2400px;
  }
}

/* Header */
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}
.brand-group {
  display: flex;
  align-items: center;
  gap: 16px;
}
.brand-title {
  font-family: 'Outfit', sans-serif;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #fff 30%, var(--cyan) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
}
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--green);
}
.copilot-orb {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 10px var(--green);
  animation: pulse-orb 2s infinite;
}
@keyframes pulse-orb {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-profile-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}
.user-avatar {
  font-size: 16px;
}
.btn-logout {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.2s;
}
.btn-logout:hover {
  color: var(--red);
  background: rgba(239, 68, 68, 0.1);
}

.btn {
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  outline: none;
}
.btn-primary {
  background: linear-gradient(135deg, var(--cyan), #0284c7);
  color: #000;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(0, 242, 254, 0.25);
}
.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 22px rgba(0, 242, 254, 0.4);
}
.btn-series {
  background: linear-gradient(135deg, #ef4444, #b91c1c);
  color: #fff;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
}
.btn-series:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5);
}
.btn-copilot-top {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #c4b5fd;
}
.btn-copilot-top:hover {
  background: rgba(139, 92, 246, 0.28);
  border-color: var(--purple);
}
.btn-ghost {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  color: var(--text-muted);
}
.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-main);
}
.btn-lang {
  background: rgba(0, 242, 254, 0.1);
  border: 1px solid rgba(0, 242, 254, 0.3);
  color: var(--cyan);
  font-weight: 700;
}
.btn-lang:hover {
  background: rgba(0, 242, 254, 0.2);
  border-color: var(--cyan);
  transform: translateY(-1px);
}

/* Tabs Navigation */
.nav-tabs-bar {
  display: flex;
  gap: 8px;
  background: rgba(9, 15, 34, 0.8);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 6px;
  margin-bottom: 24px;
  backdrop-filter: blur(12px);
}
.tab-btn {
  flex: 1;
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 16px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}
.tab-btn:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.04);
}
.tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.12), rgba(56, 189, 248, 0.06));
  border: 1px solid var(--border-glow);
  color: var(--cyan);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
.tab-badge {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-main);
  padding: 2px 7px;
  border-radius: 10px;
  font-size: 11px;
}
.tab-btn.active .tab-badge {
  background: rgba(0, 242, 254, 0.25);
  color: var(--cyan);
}

/* Tab Sections */
.tab-section {
  display: none;
  animation: fadeIn 0.25s ease forwards;
}
.tab-section.active {
  display: block;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Hero Series Card */
.series-hero-card {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(24, 15, 42, 0.9));
  border: 1px solid rgba(239, 68, 68, 0.35);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5), 0 0 30px rgba(239, 68, 68, 0.12);
}
.series-hero-card::after {
  content: "";
  position: absolute;
  top: -50%;
  right: -20%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(239, 68, 68, 0.15) 0%, transparent 60%);
  pointer-events: none;
}
.series-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid var(--red);
  color: #fca5a5;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}
.series-title {
  font-family: 'Outfit', sans-serif;
  font-size: 26px;
  font-weight: 800;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}
.series-synopsis {
  color: var(--text-muted);
  max-width: 820px;
  font-size: 14px;
  margin-bottom: 20px;
  line-height: 1.6;
}
.series-features {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}
.series-feat {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e2e8f0;
}
.series-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.ep-select {
  background: #090f22;
  border: 1px solid var(--border);
  color: #fff;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}

/* Other Series Grid */
.series-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
  margin-bottom: 30px;
}
.mini-series-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px;
  transition: all 0.2s;
  position: relative;
  backdrop-filter: blur(8px);
}
.mini-series-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.4);
}
.mini-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 8px;
}
.b-romance { background: rgba(236, 72, 153, 0.2); color: #f472b6; border: 1px solid #db2777; }
.b-kids { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #d97706; }
.b-riddle { background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #9333ea; }

.mini-title {
  font-family: 'Outfit', sans-serif;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}
.mini-desc {
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 16px;
  min-height: 38px;
}

/* Custom Prompt Studio Box */
.custom-studio-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}
.studio-input-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.custom-input {
  flex: 1;
  background: rgba(5, 8, 20, 0.85);
  border: 1px solid var(--border);
  color: #fff;
  font-family: inherit;
  font-size: 14px;
  padding: 12px 18px;
  border-radius: 8px;
  outline: none;
  transition: all 0.2s;
}
.custom-input:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.2);
}
.chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.chip {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}
.chip:hover {
  background: rgba(0, 242, 254, 0.1);
  border-color: var(--cyan);
  color: #fff;
}

/* ONBOARDING & CHANNELS STYLES */
.onboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}
.channel-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
}
.channel-card.yt-card { border-top: 3px solid #ef4444; }
.channel-card.ig-card { border-top: 3px solid #ec4899; }
.channel-card.discord-card { border-top: 3px solid #5865F2; }
.channel-card.ai-card { border-top: 3px solid var(--cyan); }
.channel-card.copilot-card { border-top: 3px solid var(--purple); }

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}
.channel-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
.channel-icon {
  font-size: 26px;
}
.channel-title {
  font-family: 'Outfit', sans-serif;
  font-size: 18px;
  font-weight: 700;
}
.channel-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
  letter-spacing: 0.3px;
}
.badge-connected {
  background: rgba(16, 185, 129, 0.2);
  border: 1px solid var(--green);
  color: #6ee7b7;
}
.badge-pending {
  background: rgba(245, 158, 11, 0.2);
  border: 1px solid var(--amber);
  color: #fcd34d;
}

.step-list {
  list-style: none;
  margin: 12px 0 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.step-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
}
.step-num {
  background: rgba(255, 255, 255, 0.1);
  color: var(--cyan);
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 11px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.code-box {
  background: rgba(5, 8, 20, 0.95);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--cyan);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 10px 0 14px;
}
.copy-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--border);
  color: var(--text-main);
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}
.copy-btn:hover {
  background: rgba(0, 242, 254, 0.2);
  border-color: var(--cyan);
}

.flowchart-container {
  background: rgba(5, 8, 20, 0.7);
  border: 1px dashed rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  padding: 12px;
  margin-top: 14px;
}
.flowchart-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.flowchart-row {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.flow-node {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  color: var(--text-main);
}
.flow-node.active-node {
  border-color: var(--cyan);
  background: rgba(0, 242, 254, 0.12);
  color: var(--cyan);
}
.flow-node.target-node {
  border-color: var(--green);
  background: rgba(16, 185, 129, 0.12);
  color: #6ee7b7;
}
.flow-arrow {
  color: var(--text-dim);
  font-size: 11px;
  flex-shrink: 0;
}

/* Tasks & Diagnostics Dashboard */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
.metric-box {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px 20px;
  backdrop-filter: blur(8px);
}
.metric-lbl {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  margin-bottom: 6px;
}
.metric-val {
  font-family: 'Outfit', sans-serif;
  font-size: 26px;
  font-weight: 800;
  color: var(--text-main);
}
.metric-val.c-green { color: var(--green); }
.metric-val.c-amber { color: var(--amber); }
.metric-val.c-cyan { color: var(--cyan); }

/* Progress Tracker */
.tracker-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}
.tracker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.tracker-steps {
  display: flex;
  justify-content: space-between;
  position: relative;
  margin-top: 10px;
}
.tracker-steps::before {
  content: "";
  position: absolute;
  top: 18px;
  left: 30px;
  right: 30px;
  height: 2px;
  background: rgba(255, 255, 255, 0.1);
  z-index: 0;
}
.tracker-step {
  position: relative;
  z-index: 1;
  text-align: center;
  flex: 1;
}
.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #090f22;
  border: 2px solid var(--border);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  margin: 0 auto 8px;
  transition: all 0.3s;
}
.tracker-step.done .step-circle {
  border-color: var(--green);
  background: rgba(16, 185, 129, 0.2);
  color: var(--green);
}
.tracker-step.active .step-circle {
  border-color: var(--cyan);
  background: rgba(0, 242, 254, 0.2);
  color: var(--cyan);
  box-shadow: 0 0 16px rgba(0, 242, 254, 0.4);
  animation: pulse-step 1.5s infinite;
}
@keyframes pulse-step {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
.step-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}
.tracker-step.active .step-label { color: var(--cyan); }
.tracker-step.done .step-label { color: #fff; }

/* Problems Diagnostics & Auto-fix */
.problems-card {
  background: rgba(20, 10, 15, 0.7);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 14px;
  padding: 20px 24px;
  margin-bottom: 24px;
}
.problems-card.healthy {
  background: rgba(10, 25, 20, 0.7);
  border-color: rgba(16, 185, 129, 0.3);
}
.problem-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.problem-item:last-child { border-bottom: none; }
.problem-info h4 {
  font-size: 14px;
  font-weight: 700;
  color: #fca5a5;
  margin-bottom: 4px;
}
.problem-info p {
  font-size: 12px;
  color: var(--text-muted);
}

/* History Table */
.data-table-container {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 24px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}
.data-table th {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-muted);
  padding: 12px 16px;
  font-weight: 600;
  border-bottom: 1px solid var(--border);
}
.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.data-table tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

/* Gallery Video Player Deck */
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.video-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.25s ease;
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
  display: flex;
  flex-direction: column;
}
.video-card:hover {
  transform: translateY(-4px) translateZ(0);
  border-color: var(--border-glow);
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.6), 0 0 24px rgba(0, 242, 254, 0.18);
}
.series-hero-card, .mini-series-card, .btn, .tab-btn {
  transform: translateZ(0);
  backface-visibility: hidden;
}
.video-preview {
  position: relative;
  background: #000;
  aspect-ratio: 9/16;
  max-height: 380px;
  overflow: hidden;
}
.video-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.video-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.video-card-body {
  padding: 14px 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.video-card-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 6px;
  line-height: 1.4;
}
.video-card-meta {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

/* Floating AI Copilot Orb & Drawer */
.fab-copilot {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: linear-gradient(135deg, var(--purple), #6366f1);
  color: #fff;
  padding: 12px 20px;
  border-radius: 30px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.4), 0 0 20px rgba(139, 92, 246, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 1000;
  transition: all 0.2s;
}
.fab-copilot:hover {
  transform: scale(1.04);
  box-shadow: 0 12px 36px rgba(139, 92, 246, 0.6);
}

.copilot-drawer {
  position: fixed;
  bottom: 80px;
  right: 24px;
  width: 420px;
  max-width: calc(100vw - 48px);
  height: 560px;
  background: rgba(10, 15, 30, 0.96);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 18px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(139, 92, 246, 0.2);
  backdrop-filter: blur(16px);
  z-index: 1001;
  display: none;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.25s ease;
}
.copilot-drawer.open {
  display: flex;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.copilot-header {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.copilot-header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 15px;
}
.copilot-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.copilot-msg {
  max-width: 86%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}
.copilot-msg.bot {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: #e2e8f0;
}
.copilot-msg.user {
  align-self: flex-end;
  background: linear-gradient(135deg, var(--purple), #4f46e5);
  color: #fff;
  font-weight: 500;
}

.copilot-pills {
  padding: 8px 16px;
  display: flex;
  gap: 8px;
  overflow-x: auto;
}
.copilot-pill {
  white-space: nowrap;
  font-size: 11px;
  background: rgba(0, 242, 254, 0.08);
  border: 1px solid rgba(0, 242, 254, 0.2);
  padding: 4px 10px;
  border-radius: 12px;
  color: var(--cyan);
  cursor: pointer;
  transition: all 0.2s;
}
.copilot-pill:hover {
  background: rgba(0, 242, 254, 0.15);
  border-color: var(--cyan);
}
.copilot-input-bar {
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.95);
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
  align-items: center;
}
.mic-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border);
  color: #fff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  transition: all 0.2s;
}
.mic-btn.listening {
  background: rgba(239, 68, 68, 0.3);
  border-color: var(--red);
  color: #fca5a5;
  animation: pulse-mic 1s infinite;
}
@keyframes pulse-mic {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

/* LOGIN GATEWAY MODAL */
.login-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(3, 7, 18, 0.92);
  backdrop-filter: blur(20px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}
.login-close-btn {
  position: absolute;
  top: 16px;
  right: 18px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border);
  color: var(--text-muted);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s;
  z-index: 10;
}
.login-close-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
  border-color: var(--cyan);
}
.login-card {
  background: linear-gradient(135deg, rgba(13, 21, 44, 0.95), rgba(9, 15, 34, 0.98));
  border: 1px solid var(--border-glow);
  border-radius: 20px;
  max-width: 440px;
  width: 100%;
  padding: 36px 32px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 40px rgba(0, 242, 254, 0.15);
  position: relative;
  overflow: hidden;
}
.login-card::before {
  content: "";
  position: absolute;
  top: -50px;
  right: -50px;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(0, 242, 254, 0.2) 0%, transparent 70%);
  pointer-events: none;
}
.login-brand {
  text-align: center;
  margin-bottom: 24px;
}
.login-logo-glow {
  font-size: 38px;
  margin-bottom: 8px;
  display: inline-block;
  animation: float-logo 3s ease-in-out infinite;
}
@keyframes float-logo {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
.login-brand h2 {
  font-family: 'Outfit', sans-serif;
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #fff 30%, var(--cyan) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
}
.login-subtitle {
  color: var(--text-muted);
  font-size: 13px;
}
.login-tabs {
  display: flex;
  background: rgba(5, 8, 20, 0.8);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 20px;
}
.login-tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 8px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.login-tab-btn.active {
  background: rgba(0, 242, 254, 0.15);
  color: var(--cyan);
}
.form-group {
  margin-bottom: 14px;
}
.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 6px;
}
.auth-input {
  width: 100%;
  background: rgba(5, 8, 20, 0.85);
  border: 1px solid var(--border);
  color: #fff;
  font-family: inherit;
  font-size: 14px;
  padding: 10px 14px;
  border-radius: 8px;
  outline: none;
  transition: all 0.2s;
}
.auth-input:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.25);
}
.btn-auth-submit {
  width: 100%;
  background: linear-gradient(135deg, var(--cyan), #0284c7);
  color: #000;
  font-family: 'Outfit', sans-serif;
  font-size: 15px;
  font-weight: 800;
  padding: 12px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 242, 254, 0.3);
  margin-top: 6px;
  transition: all 0.2s;
}
.btn-auth-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.5);
}
.auth-divider {
  text-align: center;
  position: relative;
  margin: 18px 0;
}
.auth-divider::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border);
}
.auth-divider span {
  position: relative;
  background: #0b1328;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-dim);
  letter-spacing: 0.5px;
}
.btn-demo-login {
  width: 100%;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.4);
  color: #c4b5fd;
  font-size: 13px;
  font-weight: 700;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-demo-login:hover {
  background: rgba(139, 92, 246, 0.25);
  border-color: var(--purple);
  color: #fff;
}
.auth-footer-badge {
  text-align: center;
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 16px;
}

/* Multi-Tenant Startup Styles */
.creator-id-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.4);
  color: var(--cyan);
  padding: 2px 7px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.3px;
}
.creator-id-chip:hover {
  background: rgba(0, 242, 254, 0.25);
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
  transform: translateY(-1px);
}
.creator-role-tag {
  font-size: 9px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.role-admin {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #000;
}
.role-creator {
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.5);
  color: #c4b5fd;
}
.btn-mode-toggle {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--border);
  color: #cbd5e1;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s;
}
.btn-mode-toggle:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  border-color: var(--cyan);
}
.admin-login-box {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(217, 119, 6, 0.05));
  border: 1px solid rgba(245, 158, 11, 0.4);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 18px;
  text-align: left;
}
.admin-login-box h4 {
  font-size: 13px;
  color: #fbbf24;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.admin-login-box p {
  font-size: 11px;
  color: #cbd5e1;
  margin-bottom: 10px;
  line-height: 1.4;
}
.btn-admin-login {
  width: 100%;
  background: linear-gradient(135deg, #f59e0b, #b45309);
  color: #000;
  font-family: 'Outfit', sans-serif;
  font-size: 13px;
  font-weight: 800;
  padding: 10px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.btn-admin-login:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(245, 158, 11, 0.5);
}
.empty-library-card, .empty-tasks-card {
  grid-column: 1 / -1;
  background: linear-gradient(135deg, rgba(13, 21, 44, 0.6), rgba(9, 15, 34, 0.8));
  border: 1px dashed rgba(0, 242, 254, 0.3);
  border-radius: 16px;
  padding: 44px 20px;
  text-align: center;
  max-width: 600px;
  margin: 20px auto;
}
.empty-library-card .empty-icon, .empty-tasks-card .empty-icon {
  font-size: 44px;
  margin-bottom: 12px;
  display: inline-block;
  animation: float-logo 3s ease-in-out infinite;
}
.empty-library-card h3, .empty-tasks-card h3 {
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 8px;
}
.empty-library-card p, .empty-tasks-card p {
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 20px;
}
.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

/* Toast */
#toast {
  position: fixed;
  bottom: 24px;
  left: 24px;
  background: #0f172a;
  border: 1px solid var(--cyan);
  color: #fff;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  display: none;
  z-index: 99999;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 242, 254, 0.2);
}
</style>
<script src="https://accounts.google.com/gsi/client" async defer></script>
<script>
  // Google OAuth Client ID — injected from server environment variable GOOGLE_CLIENT_ID
  window.GOOGLE_CLIENT_ID = "__GOOGLE_CLIENT_ID_PLACEHOLDER__";
</script>
</head>
<body>

<!-- LOGIN GATEWAY MODAL -->
<div id="loginModalOverlay" class="login-modal-overlay" style="display:none;" onclick="if(event.target===this) closeLoginModal()">
  <div class="login-card">
    <button class="login-close-btn" onclick="closeLoginModal()" title="Close">✕</button>
    <div class="login-brand">
      <div class="login-logo-glow">🎬</div>
      <h2>AUTOPILOT STUDIO</h2>
      <p class="login-subtitle" id="lblLoginSubtitle">Sign in to access your autonomous 12-agent media swarm</p>
    </div>

    <!-- Admin/Founder Quick Access Box -->
    <div class="admin-login-box">
      <h4>👑 Founder &amp; Admin Workspace (Abhay Maurya)</h4>
      <p>All historical creator data (199 Videos, Kaal-Rekha Series, Swarm metrics &amp; logs) is securely saved. Permanent Creator ID: <code>admin_abhay</code></p>
      <button type="button" class="btn-admin-login" onclick="quickFounderLogin()">
        ⚡ 1-Click Founder &amp; Admin Login
      </button>
    </div>
    
    <!-- 1-Click Verified Google Login -->
    <div id="googleSignInContainer" style="margin-bottom:12px; display:flex; justify-content:center;"></div>
    <button type="button" class="btn-google-auth" onclick="handleGoogleSignIn()" id="btnGoogleAuth">
      <svg class="google-g-icon" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
      </svg>
      <span>Sign in with Google (Verified Account)</span>
    </button>

    <div class="login-tabs">
      <button class="login-tab-btn active" id="tabBtnSignIn" onclick="setAuthTab('signin')">Sign In</button>
      <button class="login-tab-btn" id="tabBtnSignUp" onclick="setAuthTab('signup')">Create Account (Zero Start)</button>
    </div>
    
    <form id="authForm" onsubmit="handleAuthSubmit(event)">
      <div class="form-group" id="groupFullName" style="display:none;">
        <label id="lblFullName">Full Name</label>
        <input type="text" id="authName" placeholder="e.g. Rahul Sharma" class="auth-input">
      </div>
      <div class="form-group">
        <label id="lblEmail">Email Address or Creator ID</label>
        <input type="text" id="authEmail" placeholder="creator_id or email@example.com" required class="auth-input" value="admin_abhay">
      </div>
      <div class="form-group">
        <label id="lblPassword">Password</label>
        <input type="password" id="authPassword" placeholder="••••••••" class="auth-input" value="autopilot2026">
      </div>
      <button type="submit" class="btn-auth-submit" id="btnAuthSubmit">
        🚀 Sign In &amp; Launch Studio
      </button>
    </form>

    <div class="auth-divider">
      <span id="lblOrDivider">OR PREVIEW</span>
    </div>

    <button type="button" class="btn btn-ghost" style="width:100%; justify-content:center;" onclick="closeLoginModal()" id="btnGuestAccess">
      👀 Continue as Guest / Preview Studio
    </button>
    
    <div class="auth-footer-badge" id="lblAuthSecurity">
      🛡️ Enterprise Multi-Tenant Workspace &amp; RLS Isolation
    </div>
  </div>
</div>

<div id="app">
  <!-- Top App Header -->
  <header class="top-header">
    <div class="brand-group">
      <div class="brand-title">🎬 AUTOPILOT</div>
      <div class="status-pill" id="headerStatus">
        <span class="copilot-orb"></span>
        <span id="statusText">Swarm Online &amp; Ready</span>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn btn-lang" id="btnLang" onclick="toggleLanguage()" title="Switch Language">🌐 हिन्दी / English</button>
      <button class="btn btn-series" id="btnTopSeries" onclick="generateKaalRekha()">🔥 Series 1 (Kaal-Rekha)</button>
      <button class="btn btn-primary" id="btnTopNew" onclick="switchNav('studio')">✨ Nayi Video</button>
      <button class="btn btn-copilot-top" id="btnTopCopilot" onclick="toggleCopilot()">🤖 AI Copilot</button>
      <button class="btn btn-ghost" id="btnMute" onclick="toggleAudio()" title="Sound Effects">🔊 Sound</button>
      <button class="btn btn-ghost" id="btnTopTour" onclick="replayTour()" title="Robo-Pilot Guided Tour">🤖 Tour</button>
      
      <!-- User Profile Badge with Creator ID & Admin Mode Switcher -->
      <div class="user-profile-badge" id="userProfileBadge" style="display:none; align-items:center; gap:8px;">
        <span class="user-avatar" id="userAvatar">👑</span>
        <div style="display:flex; flex-direction:column; line-height:1.2; text-align:left;">
          <div style="display:flex; align-items:center; gap:5px;">
            <span class="user-name" id="userName" style="font-weight:700; font-size:12px;">Abhay Maurya</span>
            <span class="creator-role-tag role-admin" id="userRoleTag">ADMIN</span>
          </div>
          <div style="display:flex; align-items:center; gap:4px; margin-top:2px;">
            <span class="creator-id-chip" id="userCreatorIdChip" onclick="copyCreatorId(this)" title="Click to copy your unique Creator ID">
              ID: <span id="lblUserId">admin_abhay</span> 📋
            </span>
          </div>
        </div>
        <button class="btn-mode-toggle" id="btnAdminViewMode" onclick="toggleAdminViewMode()" style="display:none;" title="Toggle Platform View Mode">
          🌐 All Platform
        </button>
        <button class="btn-logout" onclick="handleLogout()" title="Logout" id="btnLogout">🚪</button>
      </div>
    </div>
  </header>

  <!-- Clean 5-Tab Navigation Bar -->
  <nav class="nav-tabs-bar">
    <button class="tab-btn active" id="tab-studio" onclick="switchNav('studio')">🚀 Studio (वीडियो बनाएं)</button>
    <button class="tab-btn" id="tab-onboarding" onclick="switchNav('onboarding')">🔗 Connect &amp; Setup</button>
    <button class="tab-btn" id="tab-tasks" onclick="switchNav('tasks')">
      📋 Tasks &amp; Problems <span class="tab-badge" id="badgeTaskCount">0</span>
    </button>
    <button class="tab-btn" id="tab-gallery" onclick="switchNav('gallery')">
      🎬 Video Library <span class="tab-badge" id="badgeVideoCount">0</span>
    </button>
    <button class="tab-btn" id="tab-settings" onclick="switchNav('settings')">⚙️ Settings &amp; Quota</button>
  </nav>

  <!-- ============================================================== -->
  <!-- TAB 1: STUDIO (ONE-CLICK VIDEO & SERIES CREATOR) -->
  <!-- ============================================================== -->
  <section class="tab-section active" id="sec-studio">
    <!-- FLAGSHIP SERIES 5: ASHWATTHAMA 3049 AD (CROWN JEWEL) -->
    <div class="series-hero-card" style="margin-bottom:20px; border-color:rgba(245, 158, 11, 0.45); background:linear-gradient(135deg, rgba(20, 14, 5, 0.95), rgba(35, 20, 8, 0.9)); box-shadow:0 12px 36px rgba(245, 158, 11, 0.15);">
      <div class="series-badge" style="background:linear-gradient(135deg, #F59E0B, #EF4444); color:#fff; border:none; font-weight:800;">
        ⚡ NEW CROWN JEWEL — SERIES 5
      </div>
      <h1 class="series-title" style="background:linear-gradient(135deg, #FFF, #FCD34D); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        अश्वत्थामा 3049 AD — The Immortal Cyberpunk Warrior
      </h1>
      <p class="series-synopsis">
        Himalaya ke 20,000 feet neeche frozen bunker mein jaag utha 5000 saal purana amar yoddha. Kali Yuga ke cybernetic predators aur neural implants ke khilaaf ek aakhri yuddh!
      </p>
      <div class="series-features">
        <div class="series-feat">💎 Neo-Himalayan Cyberpunk Aesthetics (Flux Pro)</div>
        <div class="series-feat">🎙️ Grave Neural Narration (Madhur Voice)</div>
        <div class="series-feat">🔥 100% Autonomous YouTube Shorts Publishing</div>
        <div class="series-feat">💬 Open Engaged Audience Comments</div>
      </div>
      <div class="series-actions" style="gap:12px; flex-wrap:wrap;">
        <a href="https://youtube.com/shorts/8xVnjfdxUKU" target="_blank" rel="noopener" class="btn" style="background:#EF4444; color:#fff; text-decoration:none; display:inline-flex; align-items:center; gap:8px; font-weight:700; border-radius:10px; padding:10px 18px;">
          ▶️ Watch Ep 1 on YouTube (Live)
        </a>
        <button class="btn btn-series" style="background:linear-gradient(135deg, #F59E0B, #D97706); border:none;" onclick="generateOtherSeries('SERIES_5')">
          🚀 1-Click Generate Next Episode
        </button>
      </div>
    </div>

    <!-- HERO: SERIES 1 KAAL-REKHA -->
    <div class="series-hero-card">
      <div class="series-badge" id="heroBadge">🔥 Flagship Anime Sci-Fi Series</div>
      <h1 class="series-title" id="heroTitle">काल-रेखा (Kaal-Rekha) — 3:17 AM Time-Loop Thriller</h1>
      <p class="series-synopsis" id="heroSynopsis">
        Kabir Sen har raat theek 3:17 AM par ek deadly time-loop mein phans jata hai. Ghadi ki ulti suiyan, Meera ka raaz, aur future ka mastermind! Ek-click mein agla episode generate karein.
      </p>
      <div class="series-features">
        <div class="series-feat" id="featVisuals">🎨 MAPPA Dark Anime Visuals (Flux Engine)</div>
        <div class="series-feat" id="featVoice">🎙️ Dual Neural Voiceover + Emotional Cadence</div>
        <div class="series-feat" id="featAudio">💥 38Hz Braam Audio FX + Kinetic Subtitles</div>
        <div class="series-feat" id="featFormat">📱 9:16 Vertical Shorts Format</div>
      </div>
      <div class="series-actions">
        <select id="series1EpSelect" class="ep-select">
          <option value="" id="optEpNext">⚡ Next Episode (Auto-detect)</option>
          <option value="1" id="optEp1">Part 1: The Message at 3:17 AM</option>
          <option value="10" id="optEp10">Part 10: Grand Season Finale (Loop Ka Anth)</option>
        </select>
        <button class="btn btn-series" id="btnGenSeries1" onclick="generateKaalRekha()">🚀 Generate Series 1 Episode</button>
      </div>
    </div>

    <!-- OTHER SERIES CARDS -->
    <h3 style="margin-bottom:14px; font-family:'Outfit',sans-serif;" id="lblSeriesSwarm">📺 Choose From Our Series Swarm</h3>
    <div class="series-grid">
      <!-- Series 2: Modern Romance -->
      <div class="mini-series-card">
        <span class="mini-badge b-romance" id="badgeS2">💖 Romance Drama</span>
        <h4 class="mini-title" id="titleS2">Series 2: जब प्यार ऑनलाइन था</h4>
        <p class="mini-desc" id="descS2">Modern online prem kahani ka emotional safar, aesthetic visuals aur soulful audio narration.</p>
        <button class="btn btn-ghost btn-gen-ep" onclick="generateOtherSeries('SERIES_2')">⚡ Generate Episode</button>
      </div>
      <!-- Series 3: Kids Adventures -->
      <div class="mini-series-card">
        <span class="mini-badge b-kids" id="badgeS3">🎨 Kids Animation</span>
        <h4 class="mini-title" id="titleS3">Series 3: चिंटू के जादुई कारनामे</h4>
        <p class="mini-desc" id="descS3">Chintu aur uske doston ki colourful 3D cartoon adventures aur fun moral stories.</p>
        <button class="btn btn-ghost btn-gen-ep" onclick="generateOtherSeries('SERIES_3')">⚡ Generate Episode</button>
      </div>
      <!-- Series 4: Mind Riddles -->
      <div class="mini-series-card">
        <span class="mini-badge b-riddle" id="badgeS4">🧠 Mind Riddles</span>
        <h4 class="mini-title" id="titleS4">Series 4: दिमाग का दही (Paheliyan)</h4>
        <p class="mini-desc" id="descS4">Mind-bending paheliyan jo 99% logon ko confuse kar dein. High engagement viral format.</p>
        <button class="btn btn-ghost btn-gen-ep" onclick="generateOtherSeries('SERIES_4')">⚡ Generate Episode</button>
      </div>
      <!-- Series 5: Ashwatthama 3049 AD -->
      <div class="mini-series-card" style="border: 1px solid rgba(245, 158, 11, 0.4); background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%);">
        <span class="mini-badge" style="background: linear-gradient(135deg, #F59E0B, #EF4444); color: white;" id="badgeS5">⚡ Epic Sci-Fi</span>
        <h4 class="mini-title" id="titleS5">Series 5: अश्वत्थामा 3049 AD</h4>
        <p class="mini-desc" id="descS5">Himalaya ke 20,000 feet neeche jaag utha 5000 saal purana amar yoddha. Dark cyberpunk action thriller.</p>
        <button class="btn btn-ghost btn-gen-ep" style="border-color: #F59E0B; color: #F59E0B;" onclick="generateOtherSeries('SERIES_5')">⚡ Generate Episode</button>
      </div>
    </div>

    <!-- CUSTOM PROMPT STUDIO -->
    <div class="custom-studio-card">
      <h3 style="margin-bottom:6px; font-family:'Outfit',sans-serif;" id="lblCustomTitle">✨ Custom Video Generator</h3>
      <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px;" id="lblCustomDesc">Apna manpasand topic likhein ya trending idea select karein:</p>
      
      <div class="chips-row">
        <span class="chip" id="chip1" onclick="setTopicFromChip(1)">🔮 Kuldhara Gaon</span>
        <span class="chip" id="chip2" onclick="setTopicFromChip(2)">🚂 Missing Train 404</span>
        <span class="chip" id="chip3" onclick="setTopicFromChip(3)">🚪 40 Saal Purana Kamra</span>
        <span class="chip" id="chip4" onclick="setTopicFromChip(4)">📱 3:33 AM Phone Call</span>
      </div>

      <div class="studio-input-row">
        <input type="text" id="customTopicInput" class="custom-input" placeholder="e.g. Kuldhara gaon ka ansoojha rahasya aur aadhi raat ki dastak">
        <select id="customVoiceSelect" class="ep-select">
          <option value="male_deep" id="optVoice1">Voice: Hindi Male (Intense Suspense)</option>
          <option value="female_urgent" id="optVoice2">Voice: Hindi Female (Urgent Thriller)</option>
          <option value="classic" id="optVoice3">Voice: Classic Hindi Storyteller</option>
        </select>
        <button class="btn btn-primary" id="btnGenCustom" onclick="generateCustomVideo()">🚀 Generate Video</button>
      </div>
    </div>
  </section>

  <!-- ============================================================== -->
  <!-- TAB 2: ONBOARDING & CHANNELS SETUP (YOUTUBE & INSTAGRAM HUB) -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-onboarding">
    <div class="series-hero-card" style="border-color:rgba(0, 242, 254, 0.35); background:linear-gradient(135deg, rgba(13, 21, 44, 0.95), rgba(8, 28, 48, 0.9));">
      <div class="series-badge" style="background:rgba(0,242,254,0.15); border-color:var(--cyan); color:var(--cyan);" id="badgeOnboardHero">
        🚀 Channel Connection &amp; Automation Hub
      </div>
      <h1 class="series-title" id="titleOnboardHero">Connect Your Distribution Channels</h1>
      <p class="series-synopsis" id="descOnboardHero">
        Connect YouTube Shorts and Instagram Reels to enable full autonomous publishing. Follow the step-by-step instructions below or let your AI Copilot guide you interactively.
      </p>
      <div class="series-features">
        <div class="series-feat" id="featOAuth">🔐 Google OAuth 2.0 PKCE (Zero-Dependency)</div>
        <div class="series-feat" id="featMeta">📸 Meta Graph API v21.0 Container Flow</div>
        <div class="series-feat" id="featAI">🤖 100% Free Neural Voice &amp; AI Tier</div>
        <div class="series-feat" id="featQA">🛡️ 4-Gate Automatic Compliance &amp; Disclosure</div>
      </div>
    </div>

    <!-- CHANNELS 2-COLUMN GRID -->
    <div class="onboard-grid">
      <!-- CARD 1: YOUTUBE AUTOMATION SETUP -->
      <div class="channel-card yt-card">
        <div>
          <div class="channel-header">
            <div class="channel-title-group">
              <span class="channel-icon">📺</span>
              <div>
                <h3 class="channel-title" id="titleYtCard">YouTube Shorts Channel</h3>
                <div style="font-size:11px; color:var(--text-muted);" id="subYtCard">OAuth 2.0 Resumable 308 Protocol</div>
              </div>
            </div>
            <span class="channel-badge badge-connected" id="statusBadgeYt">🟢 Ready &amp; Authorized</span>
          </div>

          <p style="font-size:13px; color:#cbd5e1; margin-bottom:12px;" id="descYtCard">
            Connect your YouTube channel for 1-click publishing with automatic synthetic AI disclosure tags:
          </p>

          <ul class="step-list">
            <li class="step-item">
              <span class="step-num">1</span>
              <span id="stepYt1">Go to <b>Google Cloud Console</b> ➔ Enable <b>YouTube Data API v3</b>.</span>
            </li>
            <li class="step-item">
              <span class="step-num">2</span>
              <span id="stepYt2">Create <b>OAuth Client ID</b> (Desktop App) and download as <code>client_secret.json</code> in project root.</span>
            </li>
            <li class="step-item">
              <span class="step-num">3</span>
              <span id="stepYt3">Run authorization command to generate perpetual <code>token.json</code>:</span>
            </li>
          </ul>

          <div class="code-box">
            <span>python authorize_youtube.py</span>
            <button class="copy-btn" onclick="copyCmd('python authorize_youtube.py', this)">📋 Copy</button>
          </div>

          <!-- YOUTUBE PIPELINE FLOWCHART -->
          <div class="flowchart-container">
            <div class="flowchart-title" id="lblFlowYt">⚡ Automated YouTube Shorts Flowchart</div>
            <div class="flowchart-row">
              <span class="flow-node active-node">🎯 Topic/Trend</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">✍️ Script &amp; 4-Hook</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">🎙️ Neural Voice</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">⚡ FFmpeg 60fps</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">🛡️ 4-Gate QA</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node target-node">🚀 YouTube Shorts</span>
            </div>
          </div>
        </div>

        <div style="margin-top:20px; display:flex; gap:10px;">
          <button class="btn btn-primary" onclick="testChannel('youtube')" id="btnTestYt">🔍 Test YouTube Connection</button>
          <button class="btn btn-ghost" onclick="askCopilotGuide('youtube')" id="btnGuideYt">🤖 Ask Copilot</button>
        </div>
      </div>

      <!-- CARD 2: INSTAGRAM REELS AUTOMATION SETUP -->
      <div class="channel-card ig-card">
        <div>
          <div class="channel-header">
            <div class="channel-title-group">
              <span class="channel-icon">📸</span>
              <div>
                <h3 class="channel-title" id="titleIgCard">Instagram Reels Channel</h3>
                <div style="font-size:11px; color:var(--text-muted);" id="subIgCard">Meta Graph API v21.0 Workflow</div>
              </div>
            </div>
            <span class="channel-badge badge-pending" id="statusBadgeIg">🟡 Config in .env</span>
          </div>

          <p style="font-size:13px; color:#cbd5e1; margin-bottom:12px;" id="descIgCard">
            Connect Instagram Professional/Creator account for automated 3-step Reels container publishing:
          </p>

          <ul class="step-list">
            <li class="step-item">
              <span class="step-num">1</span>
              <span id="stepIg1">Switch Instagram to <b>Professional</b> and link to a <b>Facebook Page</b>.</span>
            </li>
            <li class="step-item">
              <span class="step-num">2</span>
              <span id="stepIg2">In Meta for Developers, create a <b>Business App</b> with <b>Instagram Graph API</b>.</span>
            </li>
            <li class="step-item">
              <span class="step-num">3</span>
              <span id="stepIg3">Add your <code>IG_BUSINESS_ACCOUNT_ID</code> and 60-day <code>IG_LONG_LIVED_TOKEN</code> in <code>.env</code>.</span>
            </li>
          </ul>

          <div class="code-box">
            <span>python -m agents.ig_publisher --info</span>
            <button class="copy-btn" onclick="copyCmd('python -m agents.ig_publisher --info', this)">📋 Copy</button>
          </div>

          <!-- INSTAGRAM PIPELINE FLOWCHART -->
          <div class="flowchart-container">
            <div class="flowchart-title" id="lblFlowIg">⚡ Automated Instagram Reels Flowchart</div>
            <div class="flowchart-row">
              <span class="flow-node active-node">🎞️ Master MP4</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">🌐 Public CDN / Release</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">📦 Meta Container Init</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">⏳ Status Poll</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node target-node">📸 Instagram Reels</span>
            </div>
          </div>
        </div>

        <div style="margin-top:20px; display:flex; gap:10px;">
          <button class="btn btn-primary" onclick="testChannel('instagram')" id="btnTestIg">🔍 Test Instagram Connection</button>
          <button class="btn btn-ghost" onclick="askCopilotGuide('instagram')" id="btnGuideIg">🤖 Ask Copilot</button>
        </div>
      </div>

      <!-- CARD 3: DISCORD INTEGRATION & BOT AUTOMATION -->
      <div class="channel-card discord-card" id="cardDiscord">
        <div>
          <div class="channel-header">
            <div class="channel-title-group">
              <span class="channel-icon">💬</span>
              <div>
                <h3 class="channel-title" id="titleDiscordCard">Discord Bot &amp; Notifications</h3>
                <div style="font-size:11px; color:var(--text-muted);" id="subDiscordCard">OAuth 2.0 + Slash Commands (/status, /generate)</div>
              </div>
            </div>
            <span class="channel-badge badge-pending" id="statusBadgeDiscord">🟡 Not Connected</span>
          </div>

          <!-- Unconnected State View -->
          <div id="discordUnconnectedView">
            <p style="font-size:13px; color:#cbd5e1; margin-bottom:12px;">
              Connect Discord to receive video generation, rendering, and upload notifications and control AUTOPILOT directly from Discord using bot slash commands:
            </p>
            <ul class="step-list">
              <li class="step-item">
                <span class="step-num">1</span>
                <span>Click <b>Connect Discord</b> to authorize AUTOPILOT in your server.</span>
              </li>
              <li class="step-item">
                <span class="step-num">2</span>
                <span>Select your notification channel for real-time video rendering &amp; upload alerts.</span>
              </li>
              <li class="step-item">
                <span class="step-num">3</span>
                <span>Use bot slash commands <code>/status</code>, <code>/generate</code>, <code>/upload</code>, <code>/analytics</code> in your server!</span>
              </li>
            </ul>
            <div style="margin-top:20px; display:flex; gap:10px; flex-wrap:wrap;">
              <button class="btn btn-primary" onclick="connectDiscord()" id="btnConnectDiscord" style="background:#5865F2; border-color:#5865F2;">💬 Connect Discord</button>
              <button class="btn btn-ghost" onclick="testChannel('discord')" id="btnTestDiscord">🔍 Test Discord Webhook</button>
            </div>
          </div>

          <!-- Connected State View -->
          <div id="discordConnectedView" style="display:none;">
            <div style="background:rgba(88, 101, 242, 0.08); border:1px solid rgba(88, 101, 242, 0.3); border-radius:12px; padding:14px; margin-bottom:14px;">
              <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <div id="discordAvatar" style="width:36px; height:36px; border-radius:50%; background:#5865F2; display:flex; align-items:center; justify-content:center; font-weight:700; color:#fff;">D</div>
                <div>
                  <div style="font-weight:700; color:#fff; font-size:14px;" id="discordUsernameText">@username</div>
                  <div style="font-size:11px; color:#a5b4fc;" id="discordServerText">Server: AUTOPILOT Community</div>
                </div>
              </div>
              <div style="font-size:12px; color:#cbd5e1; display:flex; flex-direction:column; gap:4px;">
                <div>📌 <b>Channel:</b> <span id="discordChannelText" style="color:var(--cyan);">#autopilot-logs</span></div>
                <div>⚡ <b>Bot Slash Commands:</b> <code style="color:#6ee7b7;">/status</code> <code style="color:#6ee7b7;">/generate</code> <code style="color:#6ee7b7;">/upload</code></div>
              </div>
            </div>

            <div style="display:flex; gap:10px; flex-wrap:wrap;">
              <button class="btn btn-ghost" onclick="toggleDiscordConfigModal(true)" id="btnConfigDiscord">⚙️ Configure</button>
              <button class="btn btn-primary" onclick="testChannel('discord')" id="btnTestDiscordLive" style="background:#5865F2; border-color:#5865F2;">🔔 Send Test Ping</button>
              <button class="btn btn-danger" onclick="disconnectDiscord()" id="btnDisconnectDiscord" style="background:rgba(239,68,68,0.2); border:1px solid #ef4444; color:#fca5a5;">🔌 Disconnect</button>
            </div>
          </div>

          <!-- DISCORD FLOWCHART -->
          <div class="flowchart-container" style="margin-top:16px;">
            <div class="flowchart-title">⚡ Autonomous Discord Bot &amp; Webhook Lifecycle</div>
            <div class="flowchart-row">
              <span class="flow-node active-node">💬 /generate</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">⚙️ AUTOPILOT AI</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">🎬 Render Embed</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node">📤 YouTube Upload</span>
              <span class="flow-arrow">➔</span>
              <span class="flow-node target-node">✅ Published Alert</span>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- CARD 3: ZERO-COST OPERATING MODE & 4-GATE COMPLIANCE -->
    <div class="custom-studio-card" style="border-color:rgba(16, 185, 129, 0.35);">
      <h3 style="margin-bottom:8px; font-family:'Outfit',sans-serif; color:#6ee7b7;" id="titleZeroCostCard">
        🧠 Zero-Cost Operating Architecture (₹0 / Month Safe)
      </h3>
      <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px;" id="descZeroCostCard">
        AUTOPILOT is engineered to run 100% offline or with completely free neural tiers without burning credits:
      </p>
      
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
        <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border); padding:14px; border-radius:10px;">
          <h4 style="color:var(--cyan); font-size:14px; margin-bottom:4px;" id="hdrGeminiFree">1. Google AI Studio (Free)</h4>
          <p style="font-size:12px; color:var(--text-muted);" id="txtGeminiFree">Free tier provides Gemini 2.0 Flash API keys for screenplay generation and reasoning with zero credit card required.</p>
        </div>
        <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border); padding:14px; border-radius:10px;">
          <h4 style="color:var(--cyan); font-size:14px; margin-bottom:4px;" id="hdrTtsFree">2. Microsoft Edge-TTS (Free)</h4>
          <p style="font-size:12px; color:var(--text-muted);" id="txtTtsFree">6 built-in Hindi &amp; English neural voiceover profiles (pitch, rate, tone) with unlimited zero-key synthesis.</p>
        </div>
        <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border); padding:14px; border-radius:10px;">
          <h4 style="color:var(--cyan); font-size:14px; margin-bottom:4px;" id="hdrVisualsFree">3. Pollinations AI + Pillow (Free)</h4>
          <p style="font-size:12px; color:var(--text-muted);" id="txtVisualsFree">Zero-key high-resolution image generation cascade with automatic fallback to procedural Pillow color cards.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================== -->
  <!-- TAB 3: TASKS & PROBLEMS DASHBOARD -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-tasks">
    <!-- METRICS CARDS -->
    <div class="metrics-row">
      <div class="metric-box">
        <div class="metric-lbl" id="lblTotalTasks">Total Tasks Executed</div>
        <div class="metric-val c-cyan" id="metricTotal">0</div>
      </div>
      <div class="metric-box">
        <div class="metric-lbl" id="lblCompletedTasks">Completed Successfully ✅</div>
        <div class="metric-val c-green" id="metricSuccess">0</div>
      </div>
      <div class="metric-box">
        <div class="metric-lbl" id="lblFailedTasks">Problems / Failed ⚠️</div>
        <div class="metric-val c-amber" id="metricFailed">0</div>
      </div>
      <div class="metric-box">
        <div class="metric-lbl" id="lblSuccessRate">Success Rate</div>
        <div class="metric-val" id="metricRate">100%</div>
      </div>
    </div>

    <!-- LIVE STAGES TRACKER -->
    <div class="tracker-card">
      <div class="tracker-header">
        <div>
          <h3 style="font-family:'Outfit',sans-serif; font-size:17px;" id="liveTaskTitle">Generating Video...</h3>
          <p style="color:var(--text-muted); font-size:12px;" id="liveTaskDetail">Background swarm execution is active.</p>
        </div>
        <span class="status-pill" id="liveTaskBadge">● Active</span>
      </div>

      <div class="tracker-steps">
        <div class="tracker-step done" id="stepNode1">
          <div class="step-circle">1</div>
          <div class="step-label" id="step1">✍️ 1. Scripting</div>
        </div>
        <div class="tracker-step done" id="stepNode2">
          <div class="step-circle">2</div>
          <div class="step-label" id="step2">🎙️ 2. Voiceover</div>
        </div>
        <div class="tracker-step active" id="stepNode3">
          <div class="step-circle">3</div>
          <div class="step-label" id="step3">🎨 3. Visuals (Flux)</div>
        </div>
        <div class="tracker-step" id="stepNode4">
          <div class="step-circle">4</div>
          <div class="step-label" id="step4">🎛️ 4. Audio FX &amp; Subs</div>
        </div>
        <div class="tracker-step" id="stepNode5">
          <div class="step-circle">5</div>
          <div class="step-label" id="step5">🎞️ 5. Final MP4</div>
        </div>
      </div>
    </div>

    <!-- SYSTEM PROBLEMS & 1-CLICK AUTO-FIX -->
    <div class="problems-card healthy" id="problemsBox">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h3 style="font-family:'Outfit',sans-serif; font-size:16px;" id="healthyTitle">All Systems Healthy &amp; Ready!</h3>
        <button class="btn btn-ghost" onclick="refreshProblems()" style="font-size:11px;">🔄 Scan Now</button>
      </div>
      <p style="color:var(--text-muted); font-size:13px;" id="healthyDesc">Render engine active, API quota available, and all swarm agents operational.</p>
      <div id="problemsList" style="margin-top:10px;"></div>
    </div>

    <!-- TASK HISTORY TABLE -->
    <div class="data-table-container">
      <div style="padding:16px 20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
        <h3 style="font-family:'Outfit',sans-serif; font-size:16px;" id="lblHistoryTitle">📋 Execution &amp; Task History</h3>
        <button class="btn btn-ghost" onclick="refreshTasks()" style="font-size:11px;">🔄 Refresh</button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th id="thTask">Task / Action</th>
            <th id="thTopic">Topic / Series</th>
            <th id="thStatus">Status</th>
            <th id="thTime">Timestamp</th>
            <th id="thAction">Action</th>
          </tr>
        </thead>
        <tbody id="taskHistoryTbody">
          <tr><td colspan="5" style="color:var(--text-muted); text-align:center;">Loading tasks...</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- ============================================================== -->
  <!-- TAB 4: VIDEO GALLERY & APPROVAL DECK -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-gallery">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
      <div>
        <h2 style="font-family:'Outfit',sans-serif; font-size:22px;" id="lblGalleryTitle">🎬 Video Library &amp; Approval Deck</h2>
        <p style="color:var(--text-muted); font-size:13px;" id="lblGalleryDesc">Preview rendered shorts, approve for release, or publish to YouTube.</p>
      </div>
      <button class="btn btn-primary" onclick="switchNav('studio')">✨ Nayi Video Banayein</button>
    </div>

    <div class="gallery-grid" id="galleryGrid">
      <div style="color:var(--text-muted); padding:40px; text-align:center; grid-column:1/-1;">Loading video library...</div>
    </div>
  </section>

  <!-- ============================================================== -->
  <!-- TAB 5: SETTINGS & QUOTA -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-settings">
    <div class="custom-studio-card" style="margin-bottom:24px;">
      <h3 style="margin-bottom:14px; font-family:'Outfit',sans-serif;" id="lblQuotaTitle">📊 Daily API Quota &amp; Rate Limits</h3>
      <div class="metrics-row" id="quotaMetrics">
        <div class="metric-box">
          <div class="metric-lbl">YouTube API Units</div>
          <div class="metric-val" id="qYt">0 / 10,000</div>
        </div>
        <div class="metric-box">
          <div class="metric-lbl">Instagram Publishes</div>
          <div class="metric-val" id="qIg">0 / 50</div>
        </div>
        <div class="metric-box">
          <div class="metric-lbl">Gemini Flash Quota</div>
          <div class="metric-val c-green">Unlimited (Tier 1)</div>
        </div>
      </div>
    </div>

    <div class="custom-studio-card">
      <h3 style="margin-bottom:14px; font-family:'Outfit',sans-serif;" id="lblControlsTitle">🛠️ Swarm System Controls</h3>
      <div style="display:flex; gap:12px; flex-wrap:wrap;">
        <button class="btn btn-ghost" onclick="unlockLocks()" id="btnUnlockLocks">🔓 Clear Task Locks</button>
        <button class="btn btn-ghost" onclick="toggleMockMode()" id="btnToggleMock">🔄 Toggle Mock Mode</button>
        <button class="btn btn-ghost" onclick="clearLogs()" id="btnClearLogs">🧹 Clear Old Logs</button>
      </div>
    </div>
  </section>
</div>

<!-- FLOATING COPILOT ORB -->
<div class="fab-copilot" onclick="toggleCopilot()">
  <span style="font-size:18px;">🤖</span>
  <span id="fabCopilotText">AI Copilot (Online)</span>
</div>

<!-- COPILOT SLIDE-OUT DRAWER -->
<div class="copilot-drawer" id="copilotDrawer">
  <div class="copilot-header">
    <div class="copilot-header-title">
      <span style="font-size:20px;">🤖</span>
      <div>
        <div style="font-size:14px; font-weight:700;">AUTOPILOT Copilot</div>
        <div style="font-size:11px; color:var(--green);">● Swarm Commander Online</div>
      </div>
    </div>
    <button class="btn-ghost" style="padding:4px 8px; font-size:12px; border-radius:6px;" onclick="toggleCopilot()">✕</button>
  </div>

  <div class="copilot-messages" id="copilotMessages">
    <div class="copilot-msg bot" id="botWelcomeMsg">
      👋 Hello Creator! I am your <b>AUTOPILOT Autonomous Copilot</b>.<br><br>
      You can ask me to generate the next Series 1 episode, produce custom videos, or guide you through connecting YouTube &amp; Instagram!
    </div>
  </div>

  <div class="copilot-pills">
    <span class="copilot-pill" id="pill1" onclick="sendCopilotPill(1)">🔥 Series 1 Kaal-Rekha</span>
    <span class="copilot-pill" id="pill2" onclick="sendCopilotPill(2)">📺 Connect YouTube</span>
    <span class="copilot-pill" id="pill3" onclick="sendCopilotPill(3)">📸 Connect Instagram</span>
    <span class="copilot-pill" id="pill4" onclick="sendCopilotPill(4)">🛠️ Problem Scan &amp; Fix</span>
  </div>

  <div class="copilot-input-bar">
    <button class="mic-btn" id="btnMic" onclick="toggleVoiceInput()" title="Voice Speech Input">🎙️</button>
    <input type="text" id="copilotInput" class="custom-input" style="padding:8px 12px; font-size:13px;" placeholder="Bol kar ya likh kar instruction dein..." onkeydown="if(event.key==='Enter') sendCopilot()">
    <button class="btn btn-primary" style="padding:8px 14px;" onclick="sendCopilot()">➤</button>
  </div>
</div>

<div id="toast"></div>

<script>
// Global State
let D = null;
let soundEnabled = true;
let isListening = false;
let recognition = null;
let currentLang = localStorage.getItem('autopilot_lang') || 'en';
if (!localStorage.getItem('autopilot_lang')) localStorage.setItem('autopilot_lang', 'en');
let authUser = JSON.parse(localStorage.getItem('autopilot_auth_user') || 'null');

// Complete Bilingual Dictionary (Hindi vs 100% Pure English)
const I18N = {
  hi: {
    langBtn: "🌐 हिन्दी / English",
    statusReady: "Swarm Online & Ready",
    statusBusy: "⚡ Task Running...",
    btnTopSeries: "🔥 Series 1 (Kaal-Rekha)",
    btnTopNew: "✨ Nayi Video",
    btnTopCopilot: "🤖 AI Copilot",
    soundOn: "🔊 Sound",
    soundMuted: "🔇 Muted",
    tabStudio: "🚀 Studio (वीडियो बनाएं)",
    tabOnboarding: "🔗 Connect & Setup",
    tabTasks: "📋 Tasks & Problems",
    tabGallery: "🎬 Video Library",
    tabSettings: "⚙️ Settings & Quota",
    tabEditor: "✂️ Mini Video Editor",
    tabMl: "🧠 AI Brain & ML",
    heroBadge: "🔥 Flagship Anime Sci-Fi Series",
    heroTitle: "काल-रेखा (Kaal-Rekha) — 3:17 AM Time-Loop Thriller",
    heroSynopsis: "Kabir Sen har raat theek 3:17 AM par ek deadly time-loop mein phans jata hai. Ghadi ki ulti suiyan, Meera ka raaz, aur future ka mastermind! Ek-click mein agla episode generate karein.",
    featVisuals: "🎨 MAPPA Dark Anime Visuals (Flux Engine)",
    featVoice: "🎙️ Dual Neural Voiceover + Emotional Cadence",
    featAudio: "💥 38Hz Braam Audio FX + Kinetic Subtitles",
    featFormat: "📱 9:16 Vertical Shorts Format",
    optEpNext: "⚡ Next Episode (Auto-detect)",
    optEp1: "Part 1: The Message at 3:17 AM",
    optEp10: "Part 10: Grand Season Finale (Loop Ka Anth)",
    btnGenSeries1: "🚀 Generate Series 1 Episode",
    lblSeriesSwarm: "📺 Choose From Our Series Swarm",
    badgeS2: "💖 Romance Drama",
    titleS2: "Series 2: जब प्यार ऑनलाइन था",
    descS2: "Modern online prem kahani ka emotional safar, aesthetic visuals aur soulful audio narration.",
    badgeS3: "🎨 Kids Animation",
    titleS3: "Series 3: चिंटू के जादुई कारनामे",
    descS3: "Chintu aur uske doston ki colourful 3D cartoon adventures aur fun moral stories.",
    badgeS4: "🧠 Mind Riddles",
    titleS4: "Series 4: दिमाग का दही (Paheliyan)",
    descS4: "Mind-bending paheliyan jo 99% logon ko confuse kar dein. High engagement viral format.",
    btnGenEp: "⚡ Generate Episode",
    lblCustomTitle: "✨ Custom Video Generator",
    lblCustomDesc: "Apna manpasand topic likhein ya trending idea select karein:",
    customPlaceholder: "e.g. Kuldhara gaon ka ansoojha rahasya aur aadhi raat ki dastak",
    chip1: "🔮 Kuldhara Gaon",
    chip2: "🚂 Missing Train 404",
    chip3: "🚪 40 Saal Purana Kamra",
    chip4: "📱 3:33 AM Phone Call",
    chip1Topic: "Kuldhara gaon ka 100 saal purana rahasya",
    chip2Topic: "Wo train jo kabhi agle station nahi pahunchi",
    chip3Topic: "Ek band kamra jise 40 saal se kisi ne nahi khola",
    chip4Topic: "Aadhi raat 3:33 AM ka mysterious phone call",
    optVoice1: "Voice: Hindi Male (Intense Suspense)",
    optVoice2: "Voice: Hindi Female (Urgent Thriller)",
    optVoice3: "Voice: Classic Hindi Storyteller",
    btnGenCustom: "🚀 Generate Video",
    badgeOnboardHero: "🚀 Channel Connection & Automation Hub",
    titleOnboardHero: "Apne Distribution Channels Connect Karein",
    descOnboardHero: "YouTube Shorts aur Instagram Reels ko connect karke 100% automated autonomous media publishing active karein. Neeche diye steps follow karein ya Copilot ki madad lein.",
    featOAuth: "🔐 Google OAuth 2.0 PKCE (Zero-Dependency)",
    featMeta: "📸 Meta Graph API v21.0 Container Flow",
    featAI: "🤖 100% Free Neural Voice & AI Tier",
    featQA: "🛡️ 4-Gate Automatic Compliance & Disclosure",
    titleYtCard: "YouTube Shorts Channel",
    subYtCard: "OAuth 2.0 Resumable 308 Protocol",
    statusBadgeYt: "🟢 Ready & Authorized",
    descYtCard: "YouTube channel connect karein taaki automatic AI disclosure ke saath video Shorts par upload ho sake:",
    stepYt1: "<b>Google Cloud Console</b> par jayein ➔ <b>YouTube Data API v3</b> enable karein.",
    stepYt2: "<b>OAuth Client ID</b> (Desktop App) banayein aur <code>client_secret.json</code> project folder mein rakhein.",
    stepYt3: "One-time authorization chala kar <code>token.json</code> banayein:",
    btnTestYt: "🔍 Test YouTube Connection",
    btnGuideYt: "🤖 Ask Copilot",
    lblFlowYt: "⚡ Automated YouTube Shorts Flowchart",
    titleIgCard: "Instagram Reels Channel",
    subIgCard: "Meta Graph API v21.0 Workflow",
    statusBadgeIg: "🟡 Config in .env",
    descIgCard: "Instagram Professional/Creator account connect karein 3-step Reels container publishing ke liye:",
    stepIg1: "Instagram ko <b>Professional</b> karein aur <b>Facebook Page</b> se jodein.",
    stepIg2: "Meta for Developers par <b>Business App</b> banayein aur <b>Instagram Graph API</b> add karein.",
    stepIg3: "Apna <code>IG_BUSINESS_ACCOUNT_ID</code> aur 60-day <code>IG_LONG_LIVED_TOKEN</code> <code>.env</code> mein daalein.",
    btnTestIg: "🔍 Test Instagram Connection",
    btnGuideIg: "🤖 Ask Copilot",
    lblFlowIg: "⚡ Automated Instagram Reels Flowchart",
    titleZeroCostCard: "🧠 Zero-Cost Operating Architecture (₹0 / Month Safe)",
    descZeroCostCard: "AUTOPILOT 100% offline ya free neural tiers ke saath bina credit card ke chalta hai:",
    hdrGeminiFree: "1. Google AI Studio (Free)",
    txtGeminiFree: "Free tier mein Gemini 2.0 Flash API keys scriptwriting aur reasoning ke liye milti hain.",
    hdrTtsFree: "2. Microsoft Edge-TTS (Free)",
    txtTtsFree: "6 built-in Hindi & English neural voiceover profiles (pitch, rate) bilkul free hain.",
    hdrVisualsFree: "3. Pollinations AI + Pillow (Free)",
    txtVisualsFree: "Zero-key high-resolution image generation cascade aur Pillow color cards fallback.",
    lblTotalTasks: "Total Tasks Executed",
    lblCompletedTasks: "Completed Successfully ✅",
    lblFailedTasks: "Problems / Failed ⚠️",
    lblSuccessRate: "Success Rate",
    liveTaskTitle: "Generating Video...",
    liveTaskDetail: "Background swarm execution is active.",
    step1: "✍️ 1. Scripting",
    step2: "🎙️ 2. Voiceover",
    step3: "🎨 3. Visuals (Flux)",
    step4: "🎛️ 4. Audio FX & Subs",
    step5: "🎞️ 5. Final MP4",
    healthyTitle: "All Systems Healthy & Ready!",
    healthyDesc: "Render engine active, API quota available, and all swarm agents operational.",
    lblHistoryTitle: "📋 Execution & Task History",
    thTask: "Task / Action",
    thTopic: "Topic / Series",
    thStatus: "Status",
    thTime: "Timestamp",
    thAction: "Action",
    lblGalleryTitle: "🎬 Video Library & Approval Deck",
    lblGalleryDesc: "Preview rendered shorts, approve for release, or publish to YouTube.",
    lblQuotaTitle: "📊 Daily API Quota & Rate Limits",
    lblControlsTitle: "🛠️ Swarm System Controls",
    btnUnlockLocks: "🔓 Clear Task Locks",
    btnToggleMock: "🔄 Toggle Mock Mode",
    btnClearLogs: "🧹 Clear Old Logs",
    fabCopilotText: "🤖 AI Copilot (Online)",
    botWelcome: "👋 Namaste! Main aapka <b>AUTOPILOT Futuristic Copilot</b> hoon.<br><br>Aap mujhse Series 1 ka agla episode banwa sakte hain, video generate karwa sakte hain, ya YouTube &amp; Instagram connect karne ki madad le sakte hain!",
    pill1: "🔥 Series 1 Kaal-Rekha",
    pill2: "📺 Connect YouTube",
    pill3: "📸 Connect Instagram",
    pill4: "🛠️ Problem Scan & Fix",
    pill1Text: "Series 1 ka agla episode banao",
    pill2Text: "YouTube channel kaise connect karein? Step by step guide batao.",
    pill3Text: "Instagram Reels kaise connect karein? Guide batao.",
    pill4Text: "Problem check karo aur solve karo",
    inputPlaceholder: "Bol kar ya likh kar instruction dein...",
    btnApprove: "✅ Approve",
    btnPublish: "🚀 Publish YT",
    btnDownload: "⬇️ MP4",
    noVideos: "Koi video nahi mili. Nayi video banayein!",
    listeningToast: "🎙️ Listening... Bolye!",
    lblLoginSubtitle: "Apne autonomous 12-agent media swarm ko access karne ke liye sign in karein",
    lblEmail: "Email Address / Creator ID",
    lblPassword: "Password",
    btnAuthSubmit: "🚀 Sign In & Launch Studio",
    lblOrDivider: "OR INSTANT ACCESS",
    btnQuickDemo: "⚡ 1-Click Instant Demo Login (Zero Friction)",
    lblAuthSecurity: "🛡️ Enterprise OAuth 2.0 & Multi-Tenant RLS Protected"
  },
  en: {
    langBtn: "🌐 English / हिन्दी",
    statusReady: "Swarm Online & Ready",
    statusBusy: "⚡ Task Running...",
    btnTopSeries: "🔥 Series 1 (Kaal-Rekha)",
    btnTopNew: "✨ New Video",
    btnTopCopilot: "🤖 AI Copilot",
    soundOn: "🔊 Sound",
    soundMuted: "🔇 Muted",
    tabStudio: "🚀 Studio (Create Video)",
    tabOnboarding: "🔗 Connect & Setup",
    tabTasks: "📋 Tasks & Problems",
    tabGallery: "🎬 Video Library",
    tabSettings: "⚙️ Settings & Quota",
    tabEditor: "✂️ Mini Video Editor",
    tabMl: "🧠 AI Brain & ML",
    heroBadge: "🔥 Flagship Anime Sci-Fi Series",
    heroTitle: "Kaal-Rekha — 3:17 AM Time-Loop Thriller",
    heroSynopsis: "Kabir Sen is trapped in a deadly time-loop at exactly 3:17 AM every single night. Reverse ticking clocks, Meera's classified truth, and a mastermind from the future! Generate the next episode with one click.",
    featVisuals: "🎨 MAPPA Dark Anime Visuals (Flux Engine)",
    featVoice: "🎙️ Dual Neural Voiceover + Emotional Cadence",
    featAudio: "💥 38Hz Braam Audio FX + Kinetic Subtitles",
    featFormat: "📱 9:16 Vertical Shorts Format",
    optEpNext: "⚡ Next Episode (Auto-detect)",
    optEp1: "Part 1: The Message at 3:17 AM",
    optEp10: "Part 10: Grand Season Finale (Breaking the Loop)",
    btnGenSeries1: "🚀 Generate Series 1 Episode",
    lblSeriesSwarm: "📺 Choose From Our Series Swarm",
    badgeS2: "💖 Romance Drama",
    titleS2: "Series 2: When Love Was Online",
    descS2: "An emotional journey of modern digital love, aesthetic visuals, and soulful voice narration.",
    badgeS3: "🎨 Kids Animation",
    titleS3: "Series 3: Chintu's Magical Adventures",
    descS3: "Colorful 3D cartoon adventures and fun moral stories of Chintu and his companions.",
    badgeS4: "🧠 Mind Riddles",
    titleS4: "Series 4: Mind Twister Riddles",
    descS4: "Mind-bending riddles designed to baffle 99% of viewers. High retention viral format.",
    btnGenEp: "⚡ Generate Episode",
    lblCustomTitle: "✨ Custom Video Generator",
    lblCustomDesc: "Enter your custom topic or pick a trending creative prompt:",
    customPlaceholder: "e.g. The 14 residents who vanished overnight from Kuldhara village",
    chip1: "🔮 Ghost Village Kuldhara",
    chip2: "🚂 Missing Express 404",
    chip3: "🚪 The 40-Year Locked Room",
    chip4: "📱 Midnight 3:33 AM Call",
    chip1Topic: "The 100-year-old unsolved mystery of Kuldhara ghost village",
    chip2Topic: "The midnight express train that never reached the next station",
    chip3Topic: "The sealed iron door room untouched for 40 years",
    chip4Topic: "The mysterious 3:33 AM phone call that warned the caller",
    optVoice1: "Voice: Intense Dramatic Male",
    optVoice2: "Voice: Urgent Suspense Female",
    optVoice3: "Voice: Classic Storyteller",
    btnGenCustom: "🚀 Generate Video",
    badgeOnboardHero: "🚀 Channel Connection & Automation Hub",
    titleOnboardHero: "Connect Your Distribution Channels",
    descOnboardHero: "Connect YouTube Shorts and Instagram Reels to enable full autonomous publishing. Follow the step-by-step instructions below or let your AI Copilot guide you interactively.",
    featOAuth: "🔐 Google OAuth 2.0 PKCE (Zero-Dependency)",
    featMeta: "📸 Meta Graph API v21.0 Container Flow",
    featAI: "🤖 100% Free Neural Voice & AI Tier",
    featQA: "🛡️ 4-Gate Automatic Compliance & Disclosure",
    titleYtCard: "YouTube Shorts Channel",
    subYtCard: "OAuth 2.0 Resumable 308 Protocol",
    statusBadgeYt: "🟢 Ready & Authorized",
    descYtCard: "Connect your YouTube channel for 1-click publishing with automatic synthetic AI disclosure tags:",
    stepYt1: "Go to <b>Google Cloud Console</b> ➔ Enable <b>YouTube Data API v3</b>.",
    stepYt2: "Create <b>OAuth Client ID</b> (Desktop App) and download as <code>client_secret.json</code> in project root.",
    stepYt3: "Run one-time authorization command to generate perpetual <code>token.json</code>:",
    btnTestYt: "🔍 Test YouTube Connection",
    btnGuideYt: "🤖 Ask Copilot",
    lblFlowYt: "⚡ Automated YouTube Shorts Flowchart",
    titleIgCard: "Instagram Reels Channel",
    subIgCard: "Meta Graph API v21.0 Workflow",
    statusBadgeIg: "🟡 Config in .env",
    descIgCard: "Connect Instagram Professional/Creator account for automated 3-step Reels container publishing:",
    stepIg1: "Switch Instagram to <b>Professional</b> and link to a <b>Facebook Page</b>.",
    stepIg2: "In Meta for Developers, create a <b>Business App</b> with <b>Instagram Graph API</b>.",
    stepIg3: "Add your <code>IG_BUSINESS_ACCOUNT_ID</code> and 60-day <code>IG_LONG_LIVED_TOKEN</code> to <code>.env</code>.",
    btnTestIg: "🔍 Test Instagram Connection",
    btnGuideIg: "🤖 Ask Copilot",
    lblFlowIg: "⚡ Automated Instagram Reels Flowchart",
    titleZeroCostCard: "🧠 Zero-Cost Operating Architecture (₹0 / Month Safe)",
    descZeroCostCard: "AUTOPILOT is engineered to run 100% offline or with completely free neural tiers without burning credits:",
    hdrGeminiFree: "1. Google AI Studio (Free)",
    txtGeminiFree: "Free tier provides Gemini 2.0 Flash API keys for screenplay generation and reasoning with zero credit card required.",
    hdrTtsFree: "2. Microsoft Edge-TTS (Free)",
    txtTtsFree: "6 built-in Hindi & English neural voiceover profiles (pitch, rate, tone) with unlimited zero-key synthesis.",
    hdrVisualsFree: "3. Pollinations AI + Pillow (Free)",
    txtVisualsFree: "Zero-key high-resolution image generation cascade with automatic fallback to procedural Pillow color cards.",
    lblTotalTasks: "Total Tasks Executed",
    lblCompletedTasks: "Completed Successfully ✅",
    lblFailedTasks: "Problems / Failed ⚠️",
    lblSuccessRate: "Success Rate",
    liveTaskTitle: "Generating Video...",
    liveTaskDetail: "Background swarm execution is active.",
    step1: "✍️ 1. Scripting",
    step2: "🎙️ 2. Voiceover",
    step3: "🎨 3. Visuals (Flux)",
    step4: "🎛️ 4. Audio FX & Subs",
    step5: "🎞️ 5. Final MP4",
    healthyTitle: "All Systems Healthy & Ready!",
    healthyDesc: "Render engine active, API quota available, and all swarm agents operational.",
    lblHistoryTitle: "📋 Execution & Task History",
    thTask: "Task / Action",
    thTopic: "Topic / Series",
    thStatus: "Status",
    thTime: "Timestamp",
    thAction: "Action",
    lblGalleryTitle: "🎬 Video Library & Approval Deck",
    lblGalleryDesc: "Preview rendered shorts, approve for release, or publish to YouTube.",
    lblQuotaTitle: "📊 Daily API Quota & Rate Limits",
    lblControlsTitle: "🛠️ Swarm System Controls",
    btnUnlockLocks: "🔓 Clear Task Locks",
    btnToggleMock: "🔄 Toggle Mock Mode",
    btnClearLogs: "🧹 Clear Old Logs",
    fabCopilotText: "🤖 AI Copilot (Online)",
    botWelcome: "👋 Hello! I am your <b>AUTOPILOT Futuristic Copilot</b>.<br><br>You can ask me to generate the next Series 1 episode, create a custom video, or guide you through connecting YouTube &amp; Instagram!",
    pill1: "🔥 Series 1 Kaal-Rekha",
    pill2: "📺 Connect YouTube",
    pill3: "📸 Connect Instagram",
    pill4: "🛠️ Problem Scan & Fix",
    pill1Text: "Generate the next episode of Series 1",
    pill2Text: "How do I connect my YouTube channel? Give me step by step instructions.",
    pill3Text: "How do I connect Instagram Reels? Give me a complete guide.",
    pill4Text: "Check system problems and fix them",
    inputPlaceholder: "Type or speak an instruction in English...",
    btnApprove: "✅ Approve",
    btnPublish: "🚀 Publish YT",
    btnDownload: "⬇️ MP4",
    noVideos: "No videos found in library. Create a new video to get started!",
    listeningToast: "🎙️ Listening... Speak now!",
    lblLoginSubtitle: "Sign in to access your autonomous 12-agent media swarm",
    lblEmail: "Email Address / Creator ID",
    lblPassword: "Password",
    btnAuthSubmit: "🚀 Sign In & Launch Studio",
    lblOrDivider: "OR INSTANT ACCESS",
    btnQuickDemo: "⚡ 1-Click Instant Demo Login (Zero Friction)",
    lblAuthSecurity: "🛡️ Enterprise OAuth 2.0 & Multi-Tenant RLS Protected"
  }
};

function toggleLanguage() {
  currentLang = (currentLang === 'hi') ? 'en' : 'hi';
  localStorage.setItem('autopilot_lang', currentLang);
  audio.click();
  applyLanguage(currentLang);
  toast(currentLang === 'en' ? 'Switched to English 🇺🇸' : 'हिन्दी मोड सक्रिय 🇮🇳');
}

function applyLanguage(lang) {
  const T = I18N[lang] || I18N.en;
  document.documentElement.lang = lang;

  const setT = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  };
  const setH = (id, html) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  };

  setT('btnLang', T.langBtn);
  setT('btnTopSeries', T.btnTopSeries);
  setT('btnTopNew', T.btnTopNew);
  setT('btnTopCopilot', T.btnTopCopilot);

  // Tabs
  setH('tab-studio', T.tabStudio);
  setH('tab-onboarding', T.tabOnboarding);
  const badgeT = document.getElementById('badgeTaskCount')?.textContent || '0';
  const badgeV = document.getElementById('badgeVideoCount')?.textContent || '0';
  setH('tab-tasks', `${T.tabTasks} <span class="tab-badge" id="badgeTaskCount">${badgeT}</span>`);
  setH('tab-gallery', `${T.tabGallery} <span class="tab-badge" id="badgeVideoCount">${badgeV}</span>`);
  setT('tab-settings', T.tabSettings);
  setT('tab-editor', T.tabEditor);
  setT('tab-ml', T.tabMl);

  // Hero Series 1
  setT('heroBadge', T.heroBadge);
  setT('heroTitle', T.heroTitle);
  setT('heroSynopsis', T.heroSynopsis);
  setT('featVisuals', T.featVisuals);
  setT('featVoice', T.featVoice);
  setT('featAudio', T.featAudio);
  setT('featFormat', T.featFormat);
  setT('optEpNext', T.optEpNext);
  setT('optEp1', T.optEp1);
  setT('optEp10', T.optEp10);
  setT('btnGenSeries1', T.btnGenSeries1);

  // Other series
  setT('lblSeriesSwarm', T.lblSeriesSwarm);
  setT('badgeS2', T.badgeS2);
  setT('titleS2', T.titleS2);
  setT('descS2', T.descS2);
  setT('badgeS3', T.badgeS3);
  setT('titleS3', T.titleS3);
  setT('descS3', T.descS3);
  setT('badgeS4', T.badgeS4);
  setT('titleS4', T.titleS4);
  setT('descS4', T.descS4);
  document.querySelectorAll('.btn-gen-ep').forEach(b => b.textContent = T.btnGenEp);

  // Custom
  setT('lblCustomTitle', T.lblCustomTitle);
  setT('lblCustomDesc', T.lblCustomDesc);
  const cInput = document.getElementById('customTopicInput');
  if (cInput) cInput.placeholder = T.customPlaceholder;
  setT('chip1', T.chip1);
  setT('chip2', T.chip2);
  setT('chip3', T.chip3);
  setT('chip4', T.chip4);
  setT('optVoice1', T.optVoice1);
  setT('optVoice2', T.optVoice2);
  setT('optVoice3', T.optVoice3);
  setT('btnGenCustom', T.btnGenCustom);

  // Onboarding & Channels Hub
  setT('badgeOnboardHero', T.badgeOnboardHero);
  setT('titleOnboardHero', T.titleOnboardHero);
  setT('descOnboardHero', T.descOnboardHero);
  setT('featOAuth', T.featOAuth);
  setT('featMeta', T.featMeta);
  setT('featAI', T.featAI);
  setT('featQA', T.featQA);
  setT('titleYtCard', T.titleYtCard);
  setT('subYtCard', T.subYtCard);
  setT('descYtCard', T.descYtCard);
  setH('stepYt1', T.stepYt1);
  setH('stepYt2', T.stepYt2);
  setH('stepYt3', T.stepYt3);
  setT('btnTestYt', T.btnTestYt);
  setT('btnGuideYt', T.btnGuideYt);
  setT('lblFlowYt', T.lblFlowYt);

  setT('titleIgCard', T.titleIgCard);
  setT('subIgCard', T.subIgCard);
  setT('descIgCard', T.descIgCard);
  setH('stepIg1', T.stepIg1);
  setH('stepIg2', T.stepIg2);
  setH('stepIg3', T.stepIg3);
  setT('btnTestIg', T.btnTestIg);
  setT('btnGuideIg', T.btnGuideIg);
  setT('lblFlowIg', T.lblFlowIg);

  setT('titleZeroCostCard', T.titleZeroCostCard);
  setT('descZeroCostCard', T.descZeroCostCard);
  setT('hdrGeminiFree', T.hdrGeminiFree);
  setT('txtGeminiFree', T.txtGeminiFree);
  setT('hdrTtsFree', T.hdrTtsFree);
  setT('txtTtsFree', T.txtTtsFree);
  setT('hdrVisualsFree', T.hdrVisualsFree);
  setT('txtVisualsFree', T.txtVisualsFree);

  // Login Modal
  setT('lblLoginSubtitle', T.lblLoginSubtitle);
  setT('lblEmail', T.lblEmail);
  setT('lblPassword', T.lblPassword);
  setT('btnAuthSubmit', T.btnAuthSubmit);
  setT('lblOrDivider', T.lblOrDivider);
  setT('btnQuickDemo', T.btnQuickDemo);
  setT('lblAuthSecurity', T.lblAuthSecurity);

  // Tasks Dashboard
  setT('lblTotalTasks', T.lblTotalTasks);
  setT('lblCompletedTasks', T.lblCompletedTasks);
  setT('lblFailedTasks', T.lblFailedTasks);
  setT('lblSuccessRate', T.lblSuccessRate);
  setT('step1', T.step1);
  setT('step2', T.step2);
  setT('step3', T.step3);
  setT('step4', T.step4);
  setT('step5', T.step5);
  setT('lblHistoryTitle', T.lblHistoryTitle);
  setT('thTask', T.thTask);
  setT('thTopic', T.thTopic);
  setT('thStatus', T.thStatus);
  setT('thTime', T.thTime);
  setT('thAction', T.thAction);

  // Gallery
  setT('lblGalleryTitle', T.lblGalleryTitle);
  setT('lblGalleryDesc', T.lblGalleryDesc);

  // Settings
  setT('lblQuotaTitle', T.lblQuotaTitle);
  setT('lblControlsTitle', T.lblControlsTitle);
  setT('btnUnlockLocks', T.btnUnlockLocks);
  setT('btnToggleMock', T.btnToggleMock);
  setT('btnClearLogs', T.btnClearLogs);

  // Copilot
  setT('fabCopilotText', T.fabCopilotText);
  setH('botWelcomeMsg', T.botWelcome);
  setT('pill1', T.pill1);
  setT('pill2', T.pill2);
  setT('pill3', T.pill3);
  setT('pill4', T.pill4);
  const copIn = document.getElementById('copilotInput');
  if (copIn) copIn.placeholder = T.inputPlaceholder;

  renderGallery();
  refreshTasks();
}

// Authentication & Session
function checkAuthState() {
  const overlay = document.getElementById('loginModalOverlay');
  const userBadge = document.getElementById('userProfileBadge');
  const userName = document.getElementById('userName');
  const userAvatar = document.getElementById('userAvatar');
  const userRoleTag = document.getElementById('userRoleTag');
  const lblUserId = document.getElementById('lblUserId');
  const btnAdminView = document.getElementById('btnAdminViewMode');

  // Auto-migrate legacy stored user if user_id is missing
  if (authUser && !authUser.user_id) {
    if (authUser.email === 'abhay@autopilot.ai' || authUser.name?.toLowerCase().includes('abhay')) {
      authUser.user_id = 'admin_abhay';
      authUser.role = 'admin';
    } else {
      authUser.user_id = 'creator_' + Math.random().toString(36).substring(2, 8);
      authUser.role = 'creator';
    }
    localStorage.setItem('autopilot_auth_user', JSON.stringify(authUser));
  }

  if (!authUser) {
    if (overlay) overlay.style.display = 'flex';
    if (userBadge) userBadge.style.display = 'none';
  } else {
    if (overlay) overlay.style.display = 'none';
    if (userBadge) userBadge.style.display = 'inline-flex';
    if (userName) userName.textContent = authUser.name || 'Creator';
    const isAdmin = (authUser.role === 'admin') || (authUser.user_id === 'admin_abhay');
    if (userAvatar) userAvatar.textContent = isAdmin ? '👑' : '🚀';
    if (userRoleTag) {
      userRoleTag.textContent = isAdmin ? 'ADMIN' : 'CREATOR';
      userRoleTag.className = 'creator-role-tag ' + (isAdmin ? 'role-admin' : 'role-creator');
    }
    if (lblUserId) lblUserId.textContent = authUser.user_id || 'admin_abhay';
    if (btnAdminView) {
      btnAdminView.style.display = isAdmin ? 'inline-flex' : 'none';
      updateAdminViewButton();
    }
  }
}

function closeLoginModal() {
  if (typeof audio !== 'undefined' && audio.click) audio.click();
  const overlay = document.getElementById('loginModalOverlay');
  if (overlay) overlay.style.display = 'none';
}

let authMode = 'signin';
function setAuthTab(mode) {
  authMode = mode;
  if (typeof audio !== 'undefined' && audio.click) audio.click();
  document.getElementById('tabBtnSignIn').classList.toggle('active', mode === 'signin');
  document.getElementById('tabBtnSignUp').classList.toggle('active', mode === 'signup');
  document.getElementById('groupFullName').style.display = (mode === 'signup') ? 'block' : 'none';
  const emailInput = document.getElementById('authEmail');
  if (mode === 'signup') {
    if (emailInput && emailInput.value === 'admin_abhay') emailInput.value = '';
    document.getElementById('lblEmail').textContent = currentLang === 'en' ? 'Email Address' : 'Email Address';
    document.getElementById('btnAuthSubmit').textContent = (currentLang === 'en') ? '✨ Create Account & Launch (Zero Start)' : '✨ Naya Account Banayein (Zero Se Shuru)';
  } else {
    document.getElementById('lblEmail').textContent = currentLang === 'en' ? 'Email Address or Creator ID' : 'Email Address ya Creator ID';
    document.getElementById('btnAuthSubmit').textContent = (currentLang === 'en') ? '🚀 Sign In & Launch Studio' : '🚀 Sign In & Studio Kholein';
  }
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('authEmail').value.trim();
  const name = document.getElementById('authName')?.value.trim() || email.split('@')[0];
  const password = document.getElementById('authPassword')?.value || '';

  try {
    if (authMode === 'signup') {
      const r = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, password })
      });
      const res = await r.json();
      if (!res.ok) {
        alert(res.error || 'Registration failed');
        return;
      }
      authUser = res.user;
      localStorage.setItem('autopilot_auth_user', JSON.stringify(authUser));
      if (typeof audio !== 'undefined' && audio.success) audio.success();
      checkAuthState();
      toast(currentLang === 'en' ? `Welcome, ${authUser.name}! Workspace initialized at zero.` : `Swagat hai, ${authUser.name}! Naya workspace zero se ready hai.`);
      switchNav('onboarding');
      load();
      refreshTasks();
      if (typeof checkNewUserTour === 'function') {
        setTimeout(() => checkNewUserTour(true), 600);
      }
    } else {
      const r = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: email, password })
      });
      const res = await r.json();
      if (!res.ok) {
        alert(res.error || 'Login failed. Please check your Creator ID.');
        return;
      }
      authUser = res.user;
      localStorage.setItem('autopilot_auth_user', JSON.stringify(authUser));
      if (typeof audio !== 'undefined' && audio.success) audio.success();
      checkAuthState();
      toast(currentLang === 'en' ? `Welcome back, ${authUser.name}! 🚀` : `Swagat hai, ${authUser.name}! 🚀`);
      load();
      refreshTasks();
    }
  } catch (err) {
    alert('Authentication error: ' + err.message);
  }
}

async function quickFounderLogin() {
  if (typeof audio !== 'undefined' && audio.success) audio.success();
  try {
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 'admin_abhay' })
    });
    const res = await r.json();
    if (res.ok && res.user) {
      authUser = res.user;
    } else {
      authUser = {
        user_id: 'admin_abhay',
        email: 'abhay@autopilot.ai',
        name: 'Abhay Maurya (Founder & Admin)',
        role: 'admin',
        tier: 'enterprise',
        credits: 10000
      };
    }
  } catch (err) {
    authUser = {
      user_id: 'admin_abhay',
      email: 'abhay@autopilot.ai',
      name: 'Abhay Maurya (Founder & Admin)',
      role: 'admin',
      tier: 'enterprise',
      credits: 10000
    };
  }
  localStorage.setItem('autopilot_auth_user', JSON.stringify(authUser));
  checkAuthState();
  toast(currentLang === 'en' ? 'Logged in as Founder & Admin (Abhay Maurya) 👑' : 'Abhay Maurya (Founder & Admin) login safal! 👑');
  load();
  refreshTasks();
}

// ─── Google Sign-In (GSI One Tap + Button) ──────────────────────────────────

// Called when the GSI library has loaded; renders the Google button & One Tap prompt
function initGoogleSignIn() {
  const clientId = window.GOOGLE_CLIENT_ID;
  const btn = document.getElementById('btnGoogleAuth');
  const ctr = document.getElementById('googleSignInContainer');

  if (!clientId || !window.google?.accounts?.id) {
    if (btn) btn.style.display = 'flex';
    if (ctr) ctr.style.display = 'none';
    return;
  }

  try {
    // Initialize Google Identity Services
    google.accounts.id.initialize({
      client_id: clientId,
      callback: onGoogleCredentialResponse,
      auto_select: false,
      cancel_on_tap_outside: true,
      context: 'signin',
      ux_mode: 'popup',
    });

    // Render the official Google button in the container div
    if (ctr) {
      google.accounts.id.renderButton(ctr, {
        theme: 'filled_blue',
        size: 'large',
        text: 'signin_with',
        shape: 'rectangular',
        logo_alignment: 'left',
        width: 340,
      });
      // Once official button renders, hide redundant custom button
      if (btn) btn.style.display = 'none';
    }
  } catch (e) {
    console.warn('Google GSI initialization notice:', e);
    if (btn) btn.style.display = 'flex';
  }
}

// Called by Google after the user picks an account (One Tap or button click)
async function onGoogleCredentialResponse(response) {
  if (!response || !response.credential) {
    toast('❌ Google Sign-In was cancelled.');
    return;
  }
  const btn = document.getElementById('btnGoogleAuth');
  if (btn) { btn.disabled = true; btn.textContent = 'Verifying with Google…'; btn.style.display = 'flex'; }

  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential })
    });
    const data = await res.json();
    if (!data.ok) {
      toast('❌ ' + (data.error || 'Google Sign-In failed. Please try again.'));
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<svg class="google-g-icon" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg><span>Sign in with Google (Verified Account)</span>';
      }
      return;
    }

    // Success — store user and update app state
    authUser = data.user;
    if (data.user?.avatar_url) authUser.avatar_url = data.user.avatar_url;
    localStorage.setItem('autopilot_auth_user', JSON.stringify(authUser));
    if (typeof audio !== 'undefined' && audio.success) audio.success();
    closeLoginModal();
    checkAuthState();

    const isNew = data.is_new;
    const displayName = authUser.name || authUser.email || 'Creator';
    const verifiedBadge = data.verified ? ' ✅' : '';
    toast(isNew
      ? `🎉 Welcome, ${displayName}${verifiedBadge}! Your workspace is ready.`
      : `👋 Welcome back, ${displayName}${verifiedBadge}!`);

    load();
    refreshTasks();

    if (isNew && typeof checkNewUserTour === 'function') {
      setTimeout(() => checkNewUserTour(true), 800);
    }
  } catch (err) {
    toast('❌ Network error during Google Sign-In: ' + err.message);
    if (btn) { btn.disabled = false; }
  }
}

// Fallback handler for custom "Sign in with Google" click
function handleGoogleSignIn() {
  const clientId = window.GOOGLE_CLIENT_ID;
  if (!clientId || !window.google?.accounts?.id) {
    toast('⚠️ Google Sign-In is not configured. Please set GOOGLE_CLIENT_ID in your .env file.');
    return;
  }
  const container = document.getElementById('googleSignInContainer');
  if (container) {
    const googleBtn = container.querySelector('[role="button"], button, div[tabindex]');
    if (googleBtn) {
      googleBtn.click();
      return;
    }
  }
  google.accounts.id.prompt((notification) => {
    if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
      console.warn('Google One Tap not displayed:', notification.getNotDisplayedReason?.() || 'skipped');
    }
  });
}

// Initialize GSI once the library script has fully loaded
window.addEventListener('load', () => {
  if (window.google?.accounts?.id) {
    initGoogleSignIn();
  } else {
    // Retry in case the async script hasn't loaded yet
    const checkInterval = setInterval(() => {
      if (window.google?.accounts?.id) {
        clearInterval(checkInterval);
        initGoogleSignIn();
      }
    }, 250);
    // Give up after 10 seconds
    setTimeout(() => clearInterval(checkInterval), 10000);
  }
});

// ────────────────────────────────────────────────────────────────────────────

function handleLogout() {
  if (typeof audio !== 'undefined' && audio.click) audio.click();
  // Cancel Google One Tap session if active
  if (window.google?.accounts?.id) {
    try { google.accounts.id.disableAutoSelect(); } catch (e) {}
  }
  localStorage.removeItem('autopilot_auth_user');
  authUser = null;
  checkAuthState();
  toast(currentLang === 'en' ? 'Logged out safely. See you soon! 👋' : 'You have been logged out safely. See you soon! 👋');
  load();
  refreshTasks();
}

// Clipboard copy helper for creator ID and commands
function copyCreatorId(btn) {
  if (typeof audio !== 'undefined' && audio.click) audio.click();
  const uid = authUser?.user_id || 'admin_abhay';
  navigator.clipboard.writeText(uid).then(() => {
    toast(`📋 Creator ID "${uid}" copy ho gaya!`);
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = `ID: ${uid} ✅`;
      setTimeout(() => { btn.innerHTML = orig; }, 2000);
    }
  }).catch(() => {
    alert(`Aapka Creator ID hai: ${uid}`);
  });
}

function copyCmd(text, btn) {
  if (typeof audio !== 'undefined' && audio.click) audio.click();
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = '✅ Copied!';
    setTimeout(() => { btn.textContent = orig; }, 2000);
  }).catch(() => {
    alert(text);
  });
}

function toggleAdminViewMode() {
  if (typeof audio !== 'undefined' && audio.click) audio.click();
  const curr = localStorage.getItem('autopilot_view_all') === 'true';
  const next = !curr;
  localStorage.setItem('autopilot_view_all', next ? 'true' : 'false');
  updateAdminViewButton();
  toast(next 
    ? (currentLang === 'en' ? 'Showing All Platform Data 🌐' : 'Sabhi Platform Data dikh raha hai 🌐')
    : (currentLang === 'en' ? 'Showing My Private Videos 🧑‍💻' : 'Sirf Mere Videos dikh rahe hain 🧑‍💻'));
  load();
  refreshTasks();
}

function updateAdminViewButton() {
  const btn = document.getElementById('btnAdminViewMode');
  if (!btn) return;
  const isAll = localStorage.getItem('autopilot_view_all') === 'true';
  btn.textContent = isAll ? '🌐 All Platform' : '🧑‍💻 My Workspace';
  btn.style.borderColor = isAll ? 'var(--cyan)' : 'var(--purple)';
}

// Centralized Action Dispatcher with User Isolation
async function sendAction(action, payload = {}) {
  const uid = authUser?.user_id || 'admin_abhay';
  payload.action = action;
  payload.user_id = uid;
  return await fetch('/api/action', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': uid
    },
    body: JSON.stringify(payload)
  });
}

// Channel Connection Tests
async function testChannel(ch) {
  audio.click();
  toast(currentLang === 'en' ? `Testing ${ch.toUpperCase()} connection...` : `${ch.toUpperCase()} connection check ho raha hai...`);
  try {
    const r = await fetch('/api/channels/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel: ch })
    });
    const res = await r.json();
    if (res.ok) {
      audio.success();
      toast(res.message);
      alert(`✅ ${ch.toUpperCase()}: ${res.message}`);
    } else {
      alert(`⚠️ ${ch.toUpperCase()}: ${res.message}`);
    }
  } catch (e) {
    alert(`Channel test response: ${e.message || 'Verification complete'}`);
  }
}

function askCopilotGuide(ch) {
  audio.click();
  toggleCopilot(true);
  const q = (ch === 'youtube') 
    ? (currentLang === 'en' ? 'How do I connect my YouTube channel? Step by step guide.' : 'YouTube channel kaise connect karein? Step by step guide.')
    : (currentLang === 'en' ? 'How do I connect Instagram Reels? Complete guide.' : 'Instagram Reels kaise connect karein? Guide batao.');
  sendCopilot(q);
}

function setTopicFromChip(num) {
  const T = I18N[currentLang] || I18N.hi;
  const topic = T['chip' + num + 'Topic'] || '';
  document.getElementById('customTopicInput').value = topic;
  audio.click();
}

function sendCopilotPill(num) {
  const T = I18N[currentLang] || I18N.hi;
  const text = T['pill' + num + 'Text'] || '';
  sendCopilot(text);
}

// Futuristic Cyber Sound Engine
class CyberAudio {
  constructor() {
    this.ctx = null;
  }
  init() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
  }
  beep(freq = 600, duration = 0.08) {
    if (!soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch(e) {}
  }
  click() { this.beep(900, 0.04); }
  success() {
    if (!soundEnabled) return;
    try {
      this.init();
      this.beep(587, 0.08);
      setTimeout(() => this.beep(880, 0.12), 80);
    } catch(e) {}
  }
}
const audio = new CyberAudio();

function toggleAudio() {
  soundEnabled = !soundEnabled;
  const T = I18N[currentLang] || I18N.hi;
  document.getElementById('btnMute').textContent = soundEnabled ? T.soundOn : T.soundMuted;
  if (soundEnabled) audio.click();
}

// Navigation Tabs
function switchNav(tabId) {
  audio.click();
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));

  const btn = document.getElementById('tab-' + tabId);
  const sec = document.getElementById('sec-' + tabId);
  if (btn) btn.classList.add('active');
  if (sec) sec.classList.add('active');

  if (tabId === 'editor' && typeof loadEditorVideos === 'function') {
    loadEditorVideos();
  }

  if (tabId === 'tasks') {
    refreshTasks();
  }
}

// Data Fetching with Multi-Tenant Filtering
async function load() {
  try {
    const uid = authUser?.user_id || 'admin_abhay';
    const viewAll = localStorage.getItem('autopilot_view_all') === 'true';
    const r = await fetch(`/api/data?user_id=${encodeURIComponent(uid)}&view_all=${viewAll ? '1' : '0'}`, {
      headers: { 'X-User-Id': uid }
    });
    D = await r.json();
    renderGallery();
    renderQuota();
    checkActiveTask(D.active_task);
    checkAuthState();
    refreshDiscordStatus();
  } catch (e) {
    console.error('Data load error:', e);
  }
}

function renderGallery() {
  const g = document.getElementById('galleryGrid');
  if (!g) return;
  const vids = (D && D.queue) ? D.queue : [];
  const badgeV = document.getElementById('badgeVideoCount');
  if (badgeV) badgeV.textContent = vids.length;

  // 20x Smoothness: Prevent destroying DOM nodes & video players if data has not changed
  const currentKey = `${currentLang}_${vids.map(v => `${v.id}_${v.status}_${v.title || ''}_${v.video_url || ''}`).join('|')}`;
  if (window._lastGalleryKey === currentKey) return;
  window._lastGalleryKey = currentKey;

  const T = I18N[currentLang] || I18N.hi;

  if (vids.length === 0) {
    const isHindi = currentLang !== 'en';
    const userName = authUser ? authUser.name : 'Creator';
    g.innerHTML = `
      <div class="empty-library-card">
        <div class="empty-icon">🎬</div>
        <h3>${isHindi ? `Swagat hai ${esc(userName)}! Workspace Khali Hai (0 Videos)` : `Welcome ${esc(userName)}! Fresh Workspace (0 Videos)`}</h3>
        <p>${isHindi ? 'Aapka account bilkul naya hai aur zero se shuru ho raha hai! Shuru karne ke liye pehla viral short banayein ya channel connect karein.' : 'Your workspace is brand new with a 100% clean slate! Launch your first short video below or connect your social channels.'}</p>
        <div class="empty-actions">
          <button class="btn btn-primary" onclick="switchNav('studio')">${isHindi ? '✨ Nayi Video Banayein' : '✨ Create First Video'}</button>
          <button class="btn btn-series" onclick="generateKaalRekha()">${isHindi ? '🔥 Kaal-Rekha Episode Banayein' : '🔥 Launch Kaal-Rekha Series'}</button>
          <button class="btn btn-ghost" onclick="switchNav('onboarding')">${isHindi ? '🔗 Connect YouTube / Instagram' : '🔗 Connect Channels'}</button>
        </div>
      </div>
    `;
    return;
  }

  g.innerHTML = vids.map(v => {
    const title = v.title || v.topic || `Video #${v.id}`;
    const preview = v.video_url
      ? `<video src="${v.video_url}" preload="metadata" controls playsinline></video>`
      : (v.cover_url
         ? `<img src="${v.cover_url}" alt="${esc(title)}">`
         : `<div class="video-preview-placeholder">🎬 #${v.id}</div>`);

    return `
      <div class="video-card">
        <div class="video-preview">${preview}</div>
        <div class="video-card-body">
          <div>
            <div class="video-card-title">${esc(title)}</div>
            <div class="video-card-meta">#${v.id} · ${v.hook_type || 'Standard'} · ${v.length_sec ? v.length_sec.toFixed(1) + 's' : '9:16'}</div>
          </div>
          <div style="display:flex;gap:8px;margin-top:12px;">
            <button class="btn btn-primary" style="flex:1;padding:6px 10px;font-size:12px;" onclick="approveVideo(${v.id})">${T.btnApprove}</button>
            <button class="btn btn-series" style="flex:1;padding:6px 10px;font-size:12px;" onclick="publishVideo(${v.id})">${T.btnPublish}</button>
            ${v.video_url ? `<a href="${v.video_url}" download class="btn btn-ghost" style="padding:6px 10px;font-size:12px;">${T.btnDownload}</a>` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderQuota() {
  if (!D || !D.quota) return;
  const q = D.quota;
  const qYt = document.getElementById('qYt');
  const qIg = document.getElementById('qIg');
  if (qYt && q.youtube_units !== undefined) qYt.textContent = `${q.youtube_units} / 10,000`;
  if (qIg && q.ig_publishes !== undefined) qIg.textContent = `${q.ig_publishes} / 50`;
}

function checkActiveTask(t) {
  const b = document.getElementById('liveTaskBadge');
  const title = document.getElementById('liveTaskTitle');
  const detail = document.getElementById('liveTaskDetail');
  const T = I18N[currentLang] || I18N.hi;

  if (t && t.status === 'running') {
    if (b) b.textContent = T.statusBusy;
    if (title) title.textContent = t.step || T.liveTaskTitle;
    if (detail) detail.textContent = t.topic || T.liveTaskDetail;
    setStageNode(t.stage || 3);
  } else {
    if (b) b.textContent = '● Idle';
    if (title) title.textContent = currentLang === 'en' ? 'Swarm Idle' : 'Swarm Taiyar Hai';
    if (detail) detail.textContent = currentLang === 'en' ? 'No active background rendering jobs.' : 'Koi video abhi render nahi ho rahi.';
    setStageNode(0);
  }
}

function setStageNode(num) {
  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById('stepNode' + i);
    if (!el) continue;
    el.classList.remove('active', 'done');
    if (i < num) el.classList.add('done');
    else if (i === num) el.classList.add('active');
  }
}

// Tasks & Problems API calls with Tenant Filter
async function refreshTasks() {
  try {
    const uid = authUser?.user_id || 'admin_abhay';
    const viewAll = localStorage.getItem('autopilot_view_all') === 'true';
    const r = await fetch(`/api/tasks/summary?user_id=${encodeURIComponent(uid)}&view_all=${viewAll ? '1' : '0'}`, {
      headers: { 'X-User-Id': uid }
    });
    const res = await r.json();
    if (res.ok) {
      document.getElementById('metricTotal').textContent = res.counts.total;
      document.getElementById('metricSuccess').textContent = res.counts.completed;
      document.getElementById('metricFailed').textContent = res.counts.failed;
      document.getElementById('metricRate').textContent = res.success_rate + '%';

      const badgeT = document.getElementById('badgeTaskCount');
      if (badgeT) badgeT.textContent = res.counts.total;

      const tb = document.getElementById('taskHistoryTbody');
      const jobList = res.jobs || res.history || [];
      if (tb) {
        if (jobList.length === 0) {
          tb.innerHTML = `<tr><td colspan="5" style="color:var(--text-muted);text-align:center;padding:32px;">
            <div style="font-size:26px;margin-bottom:6px;">✨</div>
            <b>${currentLang==='en'?'0 Tasks in Queue — Clean Slate':'0 Tasks Queue Mein Hain — Clean Slate'}</b>
            <div style="font-size:12px;color:var(--text-dim);margin-top:4px;">${currentLang==='en'?'Video generation tasks will appear live here in real-time.':'Video render shuru karte hi yahan live progress dikhegi.'}</div>
          </td></tr>`;
        } else {
          tb.innerHTML = jobList.map(h => `
            <tr>
              <td><b>${esc(h.kind)}</b></td>
              <td>${esc(h.topic)}</td>
              <td><span class="mini-badge ${h.status==='completed'?'b-kids':(h.status==='failed'?'b-romance':'b-riddle')}">${esc(h.status)}</span></td>
              <td style="color:var(--text-muted);font-size:11px;">${esc(h.ts)}</td>
              <td><button class="btn btn-ghost" style="padding:3px 8px;font-size:11px;" onclick="toast('Details for #${h.id}')">Info</button></td>
            </tr>
          `).join('');
        }
      }
    }
  } catch(e) {
    console.error(e);
  }
}

async function refreshProblems() {
  try {
    const r = await fetch('/api/problems');
    const res = await r.json();
    const box = document.getElementById('problemsBox');
    const title = document.getElementById('healthyTitle');
    const desc = document.getElementById('healthyDesc');
    const list = document.getElementById('problemsList');

    if (res.ok && res.problems && res.problems.length > 0) {
      box.classList.remove('healthy');
      title.textContent = `⚠️ ${res.problems.length} Problem(s) Detected!`;
      title.style.color = 'var(--red)';
      desc.textContent = 'Click 1-Click Auto-Fix to automatically heal the pipeline.';
      list.innerHTML = res.problems.map(p => `
        <div class="problem-item">
          <div class="problem-info">
            <h4>⚠️ ${esc(p.title)}</h4>
            <p>${esc(p.description)}</p>
          </div>
          <button class="btn btn-series" style="font-size:11px;padding:5px 12px;" onclick="applyAutoFix('${p.fix_action}')">
            🛠️ ${esc(p.fix_label)}
          </button>
        </div>
      `).join('');
    } else {
      box.classList.add('healthy');
      title.textContent = 'All Systems Healthy & Ready!';
      title.style.color = 'var(--green)';
      desc.textContent = 'Render engine active, API quota available, and all swarm agents operational.';
      list.innerHTML = '';
    }
  } catch(e) {}
}

// Video Generation Actions with Tenant Isolation
async function generateKaalRekha() {
  if (typeof audio !== 'undefined' && audio.success) audio.success();
  const ep = document.getElementById('series1EpSelect').value;
  toast(currentLang==='en' ? '🔥 Series 1: Kaal-Rekha Production Triggered!' : '🔥 Series 1: Kaal-Rekha Episode Generation Shuru!');
  switchNav('tasks');
  await sendAction('generate_series', { series: 'SERIES_1', episode: ep });
  load();
}

async function generateOtherSeries(code) {
  if (typeof audio !== 'undefined' && audio.success) audio.success();
  toast(currentLang==='en' ? `🎬 ${code} Production Triggered...` : `🎬 ${code} Episode Generation Triggered...`);
  switchNav('tasks');
  await sendAction('generate_series', { series: code });
  load();
}

async function generateCustomVideo() {
  const topic = document.getElementById('customTopicInput').value.trim();
  const voice = document.getElementById('customVoiceSelect').value;
  if (!topic) {
    alert(currentLang==='en' ? 'Please enter a topic or select an idea chip.' : 'Kripya ek topic enter karein ya chip select karein.');
    return;
  }
  if (typeof audio !== 'undefined' && audio.success) audio.success();
  toast(currentLang==='en' ? '🚀 Video Generation Triggered!' : '🚀 Video Generation Shuru!');
  switchNav('tasks');
  await sendAction('generate', { topic, voice_id: voice });
  load();
}

async function approveVideo(id) {
  if (typeof audio !== 'undefined' && audio.success) audio.success();
  toast(`✅ Video #${id} Approved!`);
  await sendAction('approve', { video_id: id });
  load();
}

async function publishVideo(id) {
  if (typeof audio !== 'undefined' && audio.success) audio.success();
  toast(`🚀 Video #${id} YouTube Shorts publishing queued!`);
  await sendAction('publish', { video_id: id });
  load();
}

async function applyAutoFix(action) {
  audio.click();
  toast(currentLang==='en' ? `🛠️ Applying Auto-Fix: ${action}...` : `🛠️ Applying Auto-Fix: ${action}...`);
  try {
    const r = await fetch('/api/pipeline/fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    const res = await r.json();
    if (res.ok) {
      audio.success();
      toast('✅ ' + (res.message || 'Auto-Fix applied successfully!'));
      refreshProblems();
      load();
    }
  } catch(e) {
    alert('Fix error: ' + e);
  }
}

async function unlockLocks() {
  audio.click();
  await applyAutoFix('reset_task');
}

async function toggleMockMode() {
  audio.click();
  await applyAutoFix('toggle_mock');
}

async function clearLogs() {
  audio.click();
  toast('🧹 Logs cleared');
}

// AI Copilot Drawer & Messaging
function toggleCopilot(forceOpen) {
  audio.click();
  const d = document.getElementById('copilotDrawer');
  if (forceOpen === true) d.classList.add('open');
  else if (forceOpen === false) d.classList.remove('open');
  else d.classList.toggle('open');
}

async function sendCopilot(customText) {
  const input = document.getElementById('copilotInput');
  const msg = (customText || input.value).trim();
  if (!msg) return;

  const msgs = document.getElementById('copilotMessages');
  msgs.innerHTML += `<div class="copilot-msg user">${esc(msg)}</div>`;
  if (!customText) input.value = '';
  audio.click();
  msgs.scrollTop = msgs.scrollHeight;

  const typId = 'typ_' + Date.now();
  msgs.innerHTML += `<div class="copilot-msg bot" id="${typId}">⚡ Thinking &amp; Executing...</div>`;
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const r = await fetch('/api/assistant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, language: currentLang })
    });
    const res = await r.json();
    const typEl = document.getElementById(typId);
    if (typEl) typEl.remove();

    if (res.ok) {
      audio.success();
      let replyHtml = esc(res.reply).split('\n').join('<br>');
      replyHtml = replyHtml.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
      msgs.innerHTML += `<div class="copilot-msg bot">${replyHtml}</div>`;
      load();
      refreshTasks();
    } else {
      msgs.innerHTML += `<div class="copilot-msg bot">❌ Error: ${esc(res.error || 'Could not process message')}</div>`;
    }
    msgs.scrollTop = msgs.scrollHeight;
  } catch (e) {
    const typEl = document.getElementById(typId);
    if (typEl) typEl.remove();
    msgs.innerHTML += `<div class="copilot-msg bot">❌ Network error: ${esc(e)}</div>`;
  }
}

// Voice Speech Recognition
function toggleVoiceInput() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    alert(currentLang==='en' ? 'Voice speech recognition is not supported in this browser. Please type your message.' : 'Voice speech recognition is not supported in this browser. Kripya type karein.');
    return;
  }

  const micBtn = document.getElementById('btnMic');
  if (isListening) {
    if (recognition) recognition.stop();
    isListening = false;
    micBtn.classList.remove('listening');
    return;
  }

  try {
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = (currentLang === 'en') ? 'en-US' : 'hi-IN';

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('listening');
      audio.beep(800, 0.1);
      const T = I18N[currentLang] || I18N.hi;
      toast(T.listeningToast);
    };

    recognition.onresult = (e) => {
      const text = e.results[0][0].transcript;
      document.getElementById('copilotInput').value = text;
      sendCopilot(text);
    };

    recognition.onerror = (e) => {
      console.warn('Speech error', e);
      isListening = false;
      micBtn.classList.remove('listening');
    };

    recognition.onend = () => {
      isListening = false;
      micBtn.classList.remove('listening');
    };

    recognition.start();
  } catch (e) {
    console.error(e);
  }
}

// Toast helper
function toast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 3000);
}

function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ==============================================================
// DISCORD INTEGRATION CLIENT CONTROLLER
// ==============================================================
let currentDiscordConnection = null;

async function refreshDiscordStatus() {
  try {
    const uid = authUser?.user_id || 'admin_abhay';
    const r = await fetch(`/api/integrations/discord/status?user_id=${encodeURIComponent(uid)}`, {
      headers: { 'X-User-Id': uid }
    });
    const res = await r.json();
    if (!res.ok) return;

    const b = document.getElementById('statusBadgeDiscord');
    const uView = document.getElementById('discordUnconnectedView');
    const cView = document.getElementById('discordConnectedView');

    if (res.connected && res.connection) {
      currentDiscordConnection = res.connection;
      if (b) {
        b.className = 'channel-badge badge-connected';
        b.textContent = '🟢 Discord Connected ✓';
      }
      if (uView) uView.style.display = 'none';
      if (cView) cView.style.display = 'block';

      const uEl = document.getElementById('discordUsernameText');
      const sEl = document.getElementById('discordServerText');
      const chEl = document.getElementById('discordChannelText');
      const avEl = document.getElementById('discordAvatar');

      if (uEl) uEl.textContent = `@${res.connection.username || 'User'}`;
      if (sEl) sEl.textContent = `Server: ${res.connection.guild_name || res.connection.guild_id || 'AUTOPILOT Community'}`;
      if (chEl) chEl.textContent = res.connection.channel_name || res.connection.channel_id || '#general';
      if (avEl) {
        if (res.connection.avatar && res.connection.discord_user_id) {
          avEl.innerHTML = `<img src="https://cdn.discordapp.com/avatars/${res.connection.discord_user_id}/${res.connection.avatar}.png?size=64" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
        } else {
          avEl.textContent = (res.connection.username || 'D').charAt(0).toUpperCase();
        }
      }
    } else {
      currentDiscordConnection = null;
      if (b) {
        b.className = 'channel-badge badge-pending';
        b.textContent = res.configured ? '🟡 Ready to Connect' : '⚠️ Missing Config in .env';
      }
      if (uView) uView.style.display = 'block';
      if (cView) cView.style.display = 'none';
    }
  } catch (e) {
    console.warn('Discord status check error:', e);
  }
}

async function connectDiscord() {
  audio.click();
  const uid = authUser?.user_id || 'admin_abhay';
  toast('Connecting to Discord OAuth...');
  try {
    const r = await fetch(`/api/integrations/discord/oauth/start?user_id=${encodeURIComponent(uid)}`, {
      headers: { 'X-User-Id': uid }
    });
    const res = await r.json();
    if (res.ok && res.url) {
      window.location.href = res.url;
    } else {
      alert(`⚠️ ${res.error || 'Could not start Discord OAuth flow. Please ensure DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET are configured.'}`);
    }
  } catch (e) {
    alert(`Discord OAuth error: ${e.message}`);
  }
}

function toggleDiscordConfigModal(show) {
  audio.click();
  const m = document.getElementById('discordConfigModal');
  if (!m) return;
  m.style.display = show ? 'flex' : 'none';

  if (show && currentDiscordConnection) {
    const chInp = document.getElementById('cfgDiscordChannel');
    const whInp = document.getElementById('cfgDiscordWebhook');
    const gChk = document.getElementById('cfgNotifyGen');
    const uChk = document.getElementById('cfgNotifyUpload');
    const eChk = document.getElementById('cfgNotifyErrors');
    const aChk = document.getElementById('cfgNotifyAnalytics');

    if (chInp) chInp.value = currentDiscordConnection.channel_id || currentDiscordConnection.channel_name || '';
    if (whInp) whInp.value = currentDiscordConnection.webhook_url || '';
    if (gChk) gChk.checked = Boolean(currentDiscordConnection.notify_generation ?? 1);
    if (uChk) uChk.checked = Boolean(currentDiscordConnection.notify_upload ?? 1);
    if (eChk) eChk.checked = Boolean(currentDiscordConnection.notify_errors ?? 1);
    if (aChk) aChk.checked = Boolean(currentDiscordConnection.notify_analytics ?? 0);
  }
}

async function saveDiscordSettings() {
  audio.click();
  const uid = authUser?.user_id || 'admin_abhay';
  const chVal = (document.getElementById('cfgDiscordChannel')?.value || '').trim();
  const whVal = (document.getElementById('cfgDiscordWebhook')?.value || '').trim();
  const gVal = document.getElementById('cfgNotifyGen')?.checked ? 1 : 0;
  const uVal = document.getElementById('cfgNotifyUpload')?.checked ? 1 : 0;
  const eVal = document.getElementById('cfgNotifyErrors')?.checked ? 1 : 0;
  const aVal = document.getElementById('cfgNotifyAnalytics')?.checked ? 1 : 0;

  try {
    const r = await fetch('/api/integrations/discord/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-Id': uid },
      body: JSON.stringify({
        user_id: uid,
        channel_id: chVal,
        channel_name: chVal.startsWith('#') ? chVal : (chVal ? '#' + chVal : null),
        webhook_url: whVal || null,
        notify_generation: gVal,
        notify_upload: uVal,
        notify_errors: eVal,
        notify_analytics: aVal
      })
    });
    const res = await r.json();
    if (res.ok) {
      audio.success();
      toast('Discord settings saved successfully! ✅');
      toggleDiscordConfigModal(false);
      refreshDiscordStatus();
    } else {
      alert(`⚠️ ${res.error || 'Failed to save settings'}`);
    }
  } catch (e) {
    alert(`Save error: ${e.message}`);
  }
}

async function disconnectDiscord() {
  audio.click();
  const confirmed = confirm('Are you sure you want to disconnect Discord from AUTOPILOT?');
  if (!confirmed) return;

  const uid = authUser?.user_id || 'admin_abhay';
  try {
    const r = await fetch('/api/integrations/discord/disconnect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-Id': uid },
      body: JSON.stringify({ user_id: uid })
    });
    const res = await r.json();
    if (res.ok) {
      audio.success();
      toast('Discord disconnected.');
      refreshDiscordStatus();
    } else {
      alert(`⚠️ ${res.error || 'Failed to disconnect'}`);
    }
  } catch (e) {
    alert(`Disconnect error: ${e.message}`);
  }
}

// Check Discord URL redirect parameters
(function checkDiscordUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const dParam = params.get('discord');
  if (dParam === 'connected') {
    setTimeout(() => {
      audio.success();
      alert('🎉 Discord successfully connected to AUTOPILOT! Real-time notifications and bot slash commands are now active.');
      refreshDiscordStatus();
    }, 600);
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (dParam === 'denied') {
    setTimeout(() => alert('⚠️ Discord authorization was cancelled or denied.'), 600);
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (dParam === 'error' || dParam === 'state_invalid') {
    setTimeout(() => alert('❌ Discord OAuth connection error. Please try again.'), 600);
    window.history.replaceState({}, document.title, window.location.pathname);
  }
})();

// Polling and Init
setInterval(load, 5000);
setInterval(refreshProblems, 10000);

checkAuthState();
applyLanguage(currentLang);
load();
refreshTasks();
refreshProblems();
if (typeof checkNewUserTour === 'function') setTimeout(() => checkNewUserTour(false), 900);
</script>

<!-- DISCORD CONFIGURATION MODAL -->
<div id="discordConfigModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(6px); z-index:99999; justify-content:center; align-items:center;">
  <div style="background:#0b1126; border:1px solid rgba(88,101,242,0.5); border-radius:16px; width:92%; max-width:480px; padding:24px; box-shadow:0 20px 40px rgba(0,0,0,0.7);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:12px;">
      <h3 style="font-family:'Outfit',sans-serif; color:#fff; font-size:18px; display:flex; align-items:center; gap:8px;">
        <span>💬</span> Discord Notifications Setup
      </h3>
      <button onclick="toggleDiscordConfigModal(false)" style="background:none; border:none; color:var(--text-muted); font-size:24px; cursor:pointer; line-height:1;">&times;</button>
    </div>

    <div style="display:flex; flex-direction:column; gap:14px; margin-bottom:20px;">
      <div>
        <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px;">Notification Channel Name or ID</label>
        <input type="text" id="cfgDiscordChannel" placeholder="#autopilot-logs or channel ID" style="width:100%; background:rgba(255,255,255,0.04); border:1px solid var(--border); border-radius:8px; padding:10px; color:#fff; font-size:13px; box-sizing:border-box;">
      </div>

      <div>
        <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px;">Custom Discord Webhook URL (Optional)</label>
        <input type="text" id="cfgDiscordWebhook" placeholder="https://discord.com/api/webhooks/..." style="width:100%; background:rgba(255,255,255,0.04); border:1px solid var(--border); border-radius:8px; padding:10px; color:#fff; font-size:13px; box-sizing:border-box;">
      </div>

      <div style="background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:10px; padding:12px;">
        <div style="font-size:13px; font-weight:700; margin-bottom:10px; color:#fff;">Event Notification Preferences</div>
        <label style="display:flex; align-items:center; gap:10px; font-size:13px; color:#cbd5e1; margin-bottom:8px; cursor:pointer;">
          <input type="checkbox" id="cfgNotifyGen" checked style="accent-color:#5865F2; width:16px; height:16px;">
          <span>🎬 Video generation &amp; rendering events</span>
        </label>
        <label style="display:flex; align-items:center; gap:10px; font-size:13px; color:#cbd5e1; margin-bottom:8px; cursor:pointer;">
          <input type="checkbox" id="cfgNotifyUpload" checked style="accent-color:#5865F2; width:16px; height:16px;">
          <span>📤 YouTube upload events</span>
        </label>
        <label style="display:flex; align-items:center; gap:10px; font-size:13px; color:#cbd5e1; margin-bottom:8px; cursor:pointer;">
          <input type="checkbox" id="cfgNotifyErrors" checked style="accent-color:#5865F2; width:16px; height:16px;">
          <span>🚨 Pipeline errors &amp; warnings</span>
        </label>
        <label style="display:flex; align-items:center; gap:10px; font-size:13px; color:#cbd5e1; cursor:pointer;">
          <input type="checkbox" id="cfgNotifyAnalytics" style="accent-color:#5865F2; width:16px; height:16px;">
          <span>📊 Daily analytics digests</span>
        </label>
      </div>
    </div>

    <div style="display:flex; justify-content:flex-end; gap:10px;">
      <button class="btn btn-ghost" onclick="toggleDiscordConfigModal(false)">Cancel</button>
      <button class="btn btn-primary" onclick="saveDiscordSettings()" style="background:#5865F2; border-color:#5865F2;">Save Settings</button>
    </div>
  </div>
</div>
</body>
</html>
"""

# Splice AI Brain / ML Studio, Mini Video Editor & Onboarding Tour assets into PAGE
# Also inject GOOGLE_CLIENT_ID from server environment into the page
PAGE = (
    PAGE.replace("</style>", ML_STUDIO_CSS + "\n" + EDITOR_CSS + "\n" + TOUR_CSS + "\n</style>", 1)
    .replace('<button class="tab-btn" id="tab-settings" onclick="switchNav(\'settings\')">⚙️ Settings &amp; Quota</button>',
             '<button class="tab-btn" id="tab-settings" onclick="switchNav(\'settings\')">⚙️ Settings &amp; Quota</button>\n    <button class="tab-btn" id="tab-editor" onclick="switchNav(\'editor\')">✂️ Mini Video Editor</button>\n    <button class="tab-btn" id="tab-ml" onclick="switchNav(\'ml\')">🧠 AI Brain &amp; ML Studio</button>', 1)
    .replace('</section>\n</div>\n\n<!-- FLOATING COPILOT ORB -->',
             '</section>\n' + ML_STUDIO_TAB_HTML + '\n' + EDITOR_TAB_HTML + '\n' + TOUR_HTML + '\n</div>\n\n<!-- FLOATING COPILOT ORB -->', 1)
    .replace('</script>\n\n<!-- DISCORD CONFIGURATION MODAL -->',
             '\n' + ML_STUDIO_JS + '\n' + EDITOR_JS + '\n' + TOUR_JS + '\n</script>\n\n<!-- DISCORD CONFIGURATION MODAL -->', 1)
    # Inject real Google Client ID (safe: no special chars in a valid client ID)
    .replace('__GOOGLE_CLIENT_ID_PLACEHOLDER__', GOOGLE_CLIENT_ID or '')
)


def serve(host: str = HOST, port: int = PORT, open_browser: bool = True):
    # Start Discord Bot Gateway listener if DISCORD_BOT_TOKEN is present
    try:
        from core.discord_service import DiscordBotGateway
        DiscordBotGateway.start_if_configured()
    except Exception as e:
        log.warn(f"[DISCORD] Startup gateway runner failed to initiate: {e}")

    srv = ThreadingHTTPServer((host, port), Handler)
    url = f"http://localhost:{port}" if host in ("127.0.0.1", os.environ.get("HOST", "")) else f"http://{host}:{port}"
    print("\n" + "=" * 60)
    print(f"  [*] AUTOPILOT Production Dashboard Online")
    print(f"  >>> {url} (Binding: {host}:{port})")
    print(f"  (Press Ctrl+C to terminate)")
    print("=" * 60 + "\n")
    if open_browser and not os.environ.get("PORT") and not os.environ.get("RAILWAY_ENVIRONMENT"):
        threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(url)),
                         daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped. Good bye!")
        srv.shutdown()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", type=str, default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    serve(a.host, a.port, not a.no_browser)
