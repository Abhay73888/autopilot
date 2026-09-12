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

log = Logbook("dashboard")
PORT = int(os.environ.get("PORT", CONFIG.get("dashboard_port", 8765)))
# Cloud deployments (Render/Docker) set HOST env var; local runs default to localhost
HOST = os.environ.get("HOST", "127.0.0.1")

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
                "yt_video_id": r["yt_video_id"],
                "ig_media_id": r["ig_media_id"],
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


def gather_tasks_summary() -> dict:
    """Returns tasks dashboard summary with live running task, statistics, and recent job history."""
    with DB() as db:
        jobs = db.list_jobs(limit=40)
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

        return {
            "ok": True,
            "active_task": CURRENT_TASK,
            "counts": counts,
            "success_rate": success_rate,
            "jobs": jobs_list,
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
                # one_video now returns the full manifest dict with video_id
                vid = manifest.get("video_id", 0)
                if not vid:
                    # Fallback: try to get video_id from render info embedded in manifest
                    render_info = manifest.get("render", {})
                    video_path = render_info.get("video_path", "")
                    import re
                    m = re.search(r"video_(\d+)", video_path)
                    vid = int(m.group(1)) if m else 0
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

        if action in ("generate_series", "series_generate"):
            series_code = payload.get("series", "SERIES_1").upper()
            ep_num = payload.get("episode")
            if ep_num is not None and str(ep_num).isdigit():
                ep_num = int(ep_num)
            else:
                ep_num = None
            dry_run = bool(payload.get("dry_run", CONFIG.get("mock_mode")))

            def _gen_series(worker_db):
                from series.series_runner import generate_series_episode
                res = generate_series_episode(series_code=series_code, episode_num=ep_num, dry_run=dry_run)
                if not res.get("ok"):
                    raise RuntimeError(res.get("error", f"{series_code} generation failed"))
                return res

            task_name = f"{series_code} Ep {ep_num or 'Next'}"
            return run_bg_task(f"Series Generation: {task_name}", _gen_series,
                               job_id=payload.get("job_id"), action="generate_series",
                               topic=task_name, idempotency_key=payload.get("idempotency_key"),
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
                return self._json(200, gather_tasks_summary())
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
                    }
                ]
                return self._json(200, {"ok": True, "series": catalog})
            except Exception as e:
                log.error("Series catalog fail", e)
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
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 24px 100px;
}

/* Top App Header */
.top-header {
  background: rgba(9, 15, 34, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 14px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  box-shadow: 0 10px 35px -10px rgba(0, 0, 0, 0.7);
  margin-bottom: 20px;
}
.brand-group {
  display: flex;
  align-items: center;
  gap: 14px;
}
.brand-title {
  font-family: 'Outfit', sans-serif;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #ffffff 10%, var(--cyan) 90%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: var(--green);
}
.status-pill.busy {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.4);
  color: var(--amber);
  animation: pulse-busy 1.5s infinite ease-in-out;
}
@keyframes pulse-busy {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.02); }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* Primary Buttons */
.btn {
  font-family: 'Outfit', 'Inter', sans-serif;
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
  outline: none;
}
.btn:active { transform: scale(0.96); }
.btn-primary {
  background: linear-gradient(135deg, #0284c7, #0369a1);
  border-color: rgba(56, 189, 248, 0.4);
  box-shadow: 0 4px 18px rgba(2, 132, 199, 0.35);
}
.btn-primary:hover {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  box-shadow: 0 6px 24px rgba(56, 189, 248, 0.5);
  transform: translateY(-1px);
}
.btn-series {
  background: linear-gradient(135deg, #ef4444, #b91c1c);
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 4px 18px rgba(239, 68, 68, 0.35);
}
.btn-series:hover {
  background: linear-gradient(135deg, #f87171, #dc2626);
  box-shadow: 0 6px 24px rgba(239, 68, 68, 0.55);
  transform: translateY(-1px);
}
.btn-success {
  background: linear-gradient(135deg, #059669, #047857);
  border-color: rgba(16, 185, 129, 0.4);
}
.btn-success:hover {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 6px 24px rgba(16, 185, 129, 0.4);
}
.btn-ghost {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--border);
  color: var(--text-muted);
}
.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.btn-lang {
  background: rgba(0, 242, 254, 0.12);
  border: 1px solid rgba(0, 242, 254, 0.4);
  color: #c7f8fa;
  font-weight: 700;
}
.btn-lang:hover {
  background: rgba(0, 242, 254, 0.22);
  border-color: var(--cyan);
  color: #fff;
}
.btn-copilot-top {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(0, 242, 254, 0.3));
  border: 1px solid rgba(0, 242, 254, 0.5);
  color: #fff;
  box-shadow: 0 0 15px rgba(0, 242, 254, 0.25);
}
.btn-copilot-top:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.5), rgba(0, 242, 254, 0.5));
  box-shadow: 0 0 25px rgba(0, 242, 254, 0.4);
  transform: translateY(-1px);
}

/* Simple Main Navigation Bar */
.nav-tabs-bar {
  display: flex;
  gap: 8px;
  background: rgba(13, 21, 44, 0.6);
  padding: 6px;
  border-radius: 14px;
  border: 1px solid var(--border);
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.tab-btn {
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}
.tab-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.04);
}
.tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(56, 189, 248, 0.15));
  color: #fff;
  border: 1px solid rgba(0, 242, 254, 0.4);
  box-shadow: 0 4px 15px rgba(0, 242, 254, 0.15);
}
.tab-badge {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-main);
}

/* Sections */
.tab-section {
  display: none;
}
.tab-section.active {
  display: block;
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* CARDS & CONTAINERS */
.glass-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.6);
  margin-bottom: 22px;
}

/* HERO SERIES 1 CARD */
.series-hero-card {
  background: linear-gradient(135deg, rgba(20, 10, 30, 0.85) 0%, rgba(30, 15, 20, 0.85) 100%);
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 20px;
  padding: 28px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 15px 40px -10px rgba(239, 68, 68, 0.25);
  margin-bottom: 24px;
}
.series-hero-card::after {
  content: "3:17 AM";
  position: absolute;
  right: 20px;
  bottom: -15px;
  font-family: 'Outfit', sans-serif;
  font-size: 90px;
  font-weight: 900;
  color: rgba(239, 68, 68, 0.05);
  pointer-events: none;
  letter-spacing: -2px;
}
.series-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  color: #fca5a5;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}
.series-title {
  font-family: 'Outfit', sans-serif;
  font-size: 26px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 8px;
}
.series-synopsis {
  font-size: 14px;
  color: #cbd5e1;
  max-width: 750px;
  margin-bottom: 20px;
  line-height: 1.6;
}
.series-features {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}
.series-feat {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.3);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.series-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.ep-select {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 10px 14px;
  border-radius: 10px;
  font-family: inherit;
  font-size: 13px;
  outline: none;
}

/* OTHER SERIES GRID */
.series-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}
.series-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.series-card:hover {
  border-color: rgba(56, 189, 248, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
}
.series-card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
}
.series-card-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 16px;
  line-height: 1.5;
}

/* CUSTOM CREATOR FORM */
.custom-creator-box {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 24px;
}
.input-field {
  width: 100%;
  background: rgba(4, 8, 20, 0.85);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 16px;
  color: #fff;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.input-field:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
}
.prompt-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
  margin-bottom: 16px;
}
.prompt-chip {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  padding: 5px 12px;
  border-radius: 14px;
  color: var(--blue);
  cursor: pointer;
  transition: all 0.2s;
}
.prompt-chip:hover {
  background: rgba(0, 242, 254, 0.12);
  border-color: var(--cyan);
}

/* DEDICATED TASKS & PROBLEM DASHBOARD */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 22px;
}
.metric-box {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 20px;
}
.metric-val {
  font-family: 'Outfit', sans-serif;
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
  margin-bottom: 4px;
}
.metric-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* LIVE TASK MONITOR */
.live-task-banner {
  background: linear-gradient(135deg, rgba(2, 132, 199, 0.15), rgba(139, 92, 246, 0.15));
  border: 1px solid rgba(56, 189, 248, 0.4);
  border-radius: 18px;
  padding: 20px 24px;
  margin-bottom: 22px;
}
.live-task-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 10px;
}
.live-task-title {
  font-family: 'Outfit', sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}
.task-spinner-icon {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(56, 189, 248, 0.3);
  border-top-color: var(--cyan);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 5-Step Pipeline Stages Tracker */
.pipeline-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 8px;
  margin-top: 10px;
}
.pipeline-step {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px;
  font-size: 12px;
  text-align: center;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.pipeline-step.step-active {
  background: rgba(0, 242, 254, 0.12);
  border-color: var(--cyan);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
}

/* PROBLEM ALERT CENTER */
.problem-card {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(15, 23, 42, 0.9));
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.problem-title {
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: #fca5a5;
  margin-bottom: 4px;
}
.problem-desc {
  font-size: 13px;
  color: #e2e8f0;
  line-height: 1.5;
}
.healthy-banner {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.35);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: #a7f3d0;
  margin-bottom: 22px;
}

/* TASKS HISTORY TABLE */
.tasks-table {
  width: 100%;
  border-collapse: collapse;
}
.tasks-table th {
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  color: var(--text-dim);
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  letter-spacing: 0.5px;
}
.tasks-table td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 13px;
}
.tasks-table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}

/* VIDEO GALLERY (Shorts 9:16) */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.video-item {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
}
.video-item:hover {
  border-color: var(--border-glow);
  transform: translateY(-2px);
  box-shadow: 0 12px 30px -8px rgba(0, 242, 254, 0.2);
}
.video-thumb-container {
  position: relative;
  width: 100%;
  aspect-ratio: 9/16;
  background: #000;
  overflow: hidden;
}
.video-thumb-container video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.video-item-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1;
}
.video-item-title {
  font-family: 'Outfit', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  line-height: 1.4;
  margin-bottom: 8px;
}

/* FUTURISTIC COPILOT FLOATING DRAWER */
.copilot-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  background: linear-gradient(135deg, #0284c7 0%, #8b5cf6 50%, #ec4899 100%);
  color: #fff;
  padding: 12px 20px;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 10px 30px -5px rgba(139, 92, 246, 0.5), 0 0 20px rgba(0, 242, 254, 0.3);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.copilot-fab:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 15px 40px -5px rgba(139, 92, 246, 0.7), 0 0 30px rgba(0, 242, 254, 0.5);
}
.copilot-orb {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #00f2fe;
  box-shadow: 0 0 10px #00f2fe;
  animation: orb-glow 1.8s infinite ease-in-out;
}
@keyframes orb-glow {
  0%, 100% { opacity: 0.5; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.3); }
}

.copilot-drawer {
  position: fixed;
  bottom: 85px;
  right: 24px;
  width: 440px;
  max-width: calc(100vw - 40px);
  height: 600px;
  max-height: calc(100vh - 120px);
  background: rgba(10, 15, 30, 0.95);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border: 1px solid rgba(0, 242, 254, 0.4);
  border-radius: 20px;
  box-shadow: 0 25px 70px -10px rgba(0, 0, 0, 0.9), 0 0 40px rgba(0, 242, 254, 0.2);
  z-index: 1000;
  display: none;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.copilot-header {
  padding: 16px 20px;
  background: rgba(15, 23, 42, 0.8);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.copilot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.copilot-msg {
  max-width: 88%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.5;
}
.copilot-msg.user {
  align-self: flex-end;
  background: linear-gradient(135deg, #0284c7, #0369a1);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.copilot-msg.bot {
  align-self: flex-start;
  background: rgba(19, 29, 58, 0.9);
  border: 1px solid var(--border);
  color: #f1f5f9;
  border-bottom-left-radius: 4px;
}
.copilot-quick-pills {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 8px 16px;
  background: rgba(4, 8, 20, 0.7);
  border-top: 1px solid var(--border);
  white-space: nowrap;
}
.copilot-pill {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
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
  z-index: 9999;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 242, 254, 0.2);
}
</style>
</head>
<body>

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
    </div>
  </header>

  <!-- Clean 4-Tab Navigation Bar -->
  <nav class="nav-tabs-bar">
    <button class="tab-btn active" id="tab-studio" onclick="switchNav('studio')">🚀 Studio (वीडियो बनाएं)</button>
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
        <button class="btn btn-series" id="btnGenSeries1" style="padding:12px 24px;font-size:14px" onclick="generateKaalRekha()">
          🚀 Generate Series 1 Episode
        </button>
      </div>
    </div>

    <!-- OTHER SERIES CATALOG GRID -->
    <h2 style="font-family:'Outfit';font-size:19px;color:#fff;margin-bottom:14px" id="lblSeriesSwarm">📺 Choose From Our Series Swarm</h2>
    <div class="series-grid" id="seriesGrid">
      <div class="series-card">
        <div>
          <span class="series-badge" style="background:rgba(236,72,153,0.15);color:#f472b6;border-color:rgba(236,72,153,0.4)" id="badgeS2">💖 Romance Drama</span>
          <div class="series-card-title" id="titleS2">Series 2: जब प्यार ऑनलाइन था</div>
          <div class="series-card-desc" id="descS2">Modern online prem kahani ka emotional safar, aesthetic visuals aur soulful audio narration.</div>
        </div>
        <button class="btn btn-ghost btn-gen-ep" style="border-color:rgba(236,72,153,0.4)" onclick="generateSeries('SERIES_2')">⚡ Generate Episode</button>
      </div>

      <div class="series-card">
        <div>
          <span class="series-badge" style="background:rgba(52,211,153,0.15);color:#34d399;border-color:rgba(52,211,153,0.4)" id="badgeS3">🎨 Kids Animation</span>
          <div class="series-card-title" id="titleS3">Series 3: चिंटू के जादुई कारनामे</div>
          <div class="series-card-desc" id="descS3">Chintu aur uske doston ki colourful 3D cartoon adventures aur fun moral stories.</div>
        </div>
        <button class="btn btn-ghost btn-gen-ep" style="border-color:rgba(52,211,153,0.4)" onclick="generateSeries('SERIES_3')">⚡ Generate Episode</button>
      </div>

      <div class="series-card">
        <div>
          <span class="series-badge" style="background:rgba(251,191,36,0.15);color:#fbbf24;border-color:rgba(251,191,36,0.4)" id="badgeS4">🧠 Mind Riddles</span>
          <div class="series-card-title" id="titleS4">Series 4: दिमाग का दही (Paheliyan)</div>
          <div class="series-card-desc" id="descS4">Mind-bending paheliyan jo 99% logon ko confuse kar dein. High engagement viral format.</div>
        </div>
        <button class="btn btn-ghost btn-gen-ep" style="border-color:rgba(251,191,36,0.4)" onclick="generateSeries('SERIES_4')">⚡ Generate Episode</button>
      </div>
    </div>

    <!-- CUSTOM STORY / TOPIC CREATOR -->
    <div class="custom-creator-box">
      <h2 style="font-family:'Outfit';font-size:18px;color:#fff;margin-bottom:6px" id="lblCustomTitle">✨ Custom Video Generator</h2>
      <p style="font-size:13px;color:var(--text-muted);margin-bottom:14px" id="lblCustomDesc">Apna manpasand topic likhein ya trending idea select karein:</p>
      <input type="text" id="customTopicInput" class="input-field" placeholder="e.g. Kuldhara gaon ka ansoojha rahasya aur aadhi raat ki dastak">
      <div class="prompt-chips">
        <span class="prompt-chip" id="chip1" onclick="setTopicFromChip(1)">🔮 Kuldhara Gaon</span>
        <span class="prompt-chip" id="chip2" onclick="setTopicFromChip(2)">🚂 Missing Train 404</span>
        <span class="prompt-chip" id="chip3" onclick="setTopicFromChip(3)">🚪 40 Saal Purana Kamra</span>
        <span class="prompt-chip" id="chip4" onclick="setTopicFromChip(4)">📱 3:33 AM Phone Call</span>
      </div>
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
        <select id="customVoiceSelect" class="ep-select">
          <option value="hi_m_intense" id="optVoice1">Voice: Hindi Male (Intense Suspense)</option>
          <option value="hi_f_urgent" id="optVoice2">Voice: Hindi Female (Urgent Thriller)</option>
          <option value="hi_m_narrator" id="optVoice3">Voice: Classic Hindi Storyteller</option>
        </select>
        <button class="btn btn-primary" id="btnGenCustom" style="padding:11px 22px" onclick="generateCustomVideo()">🚀 Generate Video</button>
      </div>
    </div>
  </section>

  <!-- ============================================================== -->
  <!-- TAB 2: TASKS & PROBLEMS DASHBOARD -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-tasks">
    <!-- STATS COUNTERS -->
    <div class="metrics-row">
      <div class="metric-box">
        <div class="metric-val" id="metricTotalTasks">0</div>
        <div class="metric-label" id="lblTotalTasks">Total Tasks Executed</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color:var(--green)" id="metricCompletedTasks">0</div>
        <div class="metric-label" id="lblCompletedTasks">Completed Successfully ✅</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color:var(--red)" id="metricFailedTasks">0</div>
        <div class="metric-label" id="lblFailedTasks">Problems / Failed ⚠️</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color:var(--cyan)" id="metricSuccessRate">100%</div>
        <div class="metric-label" id="lblSuccessRate">Success Rate</div>
      </div>
    </div>

    <!-- LIVE ACTIVE TASK BANNER -->
    <div class="live-task-banner" id="liveTaskBanner" style="display:none">
      <div class="live-task-head">
        <div class="live-task-title">
          <span class="task-spinner-icon"></span>
          <span id="liveTaskName">Generating Video...</span>
        </div>
        <span class="status-pill busy" id="liveTaskTimer">In Progress</span>
      </div>
      <div style="font-size:13px;color:#cbd5e1;margin-bottom:12px" id="liveTaskDetail">
        Background swarm execution is active.
      </div>
      <div class="pipeline-steps">
        <div class="pipeline-step step-active" id="step1">✍️ 1. Scripting</div>
        <div class="pipeline-step step-active" id="step2">🎙️ 2. Voiceover</div>
        <div class="pipeline-step step-active" id="step3">🎨 3. Visuals (Flux)</div>
        <div class="pipeline-step step-active" id="step4">🎛️ 4. Audio FX &amp; Subs</div>
        <div class="pipeline-step step-active" id="step5">🎞️ 5. Final MP4</div>
      </div>
    </div>

    <!-- SYSTEM PROBLEM & ERROR ALERT CENTER -->
    <div id="problemSection"></div>

    <!-- RECENT TASKS EXECUTION HISTORY -->
    <div class="glass-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <h2 style="font-family:'Outfit';font-size:18px;color:#fff" id="lblHistoryTitle">📋 Execution &amp; Task History</h2>
        <button class="btn btn-ghost" onclick="refreshTasks()">🔄 Refresh</button>
      </div>
      <div style="overflow-x:auto">
        <table class="tasks-table">
          <thead>
            <tr>
              <th id="thTask">Task / Action</th>
              <th id="thTopic">Topic / Series</th>
              <th id="thStatus">Status</th>
              <th id="thTime">Timestamp</th>
              <th id="thAction">Action</th>
            </tr>
          </thead>
          <tbody id="tasksTableBody">
            <tr><td colspan="5" style="color:var(--text-muted)">Loading tasks history...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ============================================================== -->
  <!-- TAB 3: VIDEO GALLERY -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-gallery">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px">
      <div>
        <h2 style="font-family:'Outfit';font-size:20px;color:#fff" id="lblGalleryTitle">🎬 Video Library &amp; Approval Deck</h2>
        <p style="font-size:13px;color:var(--text-muted)" id="lblGalleryDesc">Preview rendered shorts, approve for release, or publish to YouTube.</p>
      </div>
      <button class="btn btn-ghost" onclick="load()">🔄 Refresh</button>
    </div>
    <div class="video-grid" id="videoGrid"></div>
  </section>

  <!-- ============================================================== -->
  <!-- TAB 4: SETTINGS & QUOTA -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-settings">
    <div class="glass-card">
      <h2 style="font-family:'Outfit';font-size:18px;color:#fff;margin-bottom:16px" id="lblQuotaTitle">📊 Daily API Quota &amp; Rate Limits</h2>
      <div id="quotaContainer" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:16px"></div>
    </div>

    <div class="glass-card">
      <h2 style="font-family:'Outfit';font-size:18px;color:#fff;margin-bottom:16px" id="lblControlsTitle">🛠️ Swarm System Controls</h2>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <button class="btn btn-ghost" id="btnUnlockLocks" onclick="applyFix('reset_task')">🔓 Clear Task Locks</button>
        <button class="btn btn-ghost" id="btnToggleMock" onclick="applyFix('toggle_mock')">🔄 Toggle Mock Mode</button>
        <button class="btn btn-ghost" id="btnClearLogs" onclick="act('clear_logs', 0)">🧹 Clear Old Logs</button>
      </div>
    </div>
  </section>
</div>

<!-- ============================================================== -->
<!-- 100x FUTURISTIC AI COPILOT FLOATING DRAWER -->
<!-- ============================================================== -->
<div class="copilot-fab" onclick="toggleCopilot()">
  <span class="copilot-orb"></span>
  <span id="fabCopilotText">🤖 AI Copilot (Online)</span>
</div>

<div class="copilot-drawer" id="copilotDrawer">
  <div class="copilot-header">
    <div style="display:flex;align-items:center;gap:8px">
      <span class="copilot-orb"></span>
      <span style="font-family:'Outfit';font-weight:700;color:#fff">AUTOPILOT Copilot</span>
    </div>
    <button class="btn btn-ghost" style="padding:2px 8px;border-radius:50%" onclick="toggleCopilot()">✕</button>
  </div>

  <div class="copilot-messages" id="copilotMessages">
    <div class="copilot-msg bot" id="botWelcomeMsg">
      👋 Namaste! Main aapka <b>AUTOPILOT Futuristic Copilot</b> hoon.<br><br>
      Aap mujhse Series 1 ka agla episode banwa sakte hain, video generate karwa sakte hain, ya koi bhi problem check aur fix karwa sakte hain!
    </div>
  </div>

  <div class="copilot-quick-pills">
    <span class="copilot-pill" id="pill1" onclick="sendCopilotPill(1)">🔥 Series 1 Kaal-Rekha</span>
    <span class="copilot-pill" id="pill2" onclick="sendCopilotPill(2)">🛠️ Problem Scan &amp; Fix</span>
    <span class="copilot-pill" id="pill3" onclick="sendCopilotPill(3)">📋 Task Status</span>
    <span class="copilot-pill" id="pill4" onclick="sendCopilotPill(4)">💡 Viral Ideas</span>
  </div>

  <div class="copilot-input-bar">
    <button class="mic-btn" id="btnMic" onclick="toggleVoiceInput()" title="Voice Input (Speech-to-Text)">🎙️</button>
    <input type="text" id="copilotInput" class="input-field" placeholder="Bol kar ya likh kar instruction dein..." onkeydown="if(event.key==='Enter') submitCopilot()">
    <button class="btn btn-primary" style="padding:8px 14px" onclick="submitCopilot()">🚀</button>
  </div>
</div>

<div id="toast"></div>

<script>
// Global State
let D = null;
let soundEnabled = true;
let isListening = false;
let recognition = null;
let currentLang = localStorage.getItem('autopilot_lang') || 'hi';

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
    tabTasks: "📋 Tasks & Problems",
    tabGallery: "🎬 Video Library",
    tabSettings: "⚙️ Settings & Quota",
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
    botWelcome: "👋 Namaste! Main aapka <b>AUTOPILOT Futuristic Copilot</b> hoon.<br><br>Aap mujhse Series 1 ka agla episode banwa sakte hain, video generate karwa sakte hain, ya koi bhi problem check aur fix karwa sakte hain!",
    pill1: "🔥 Series 1 Kaal-Rekha",
    pill2: "🛠️ Problem Scan & Fix",
    pill3: "📋 Task Status",
    pill4: "💡 Viral Ideas",
    pill1Text: "Series 1 ka agla episode banao",
    pill2Text: "Problem check karo aur solve karo",
    pill3Text: "Kitne task hue aur status kya hai?",
    pill4Text: "5 viral mystery topic ideas batao",
    inputPlaceholder: "Bol kar ya likh kar instruction dein...",
    btnApprove: "✅ Approve",
    btnPublish: "🚀 Publish YT",
    btnDownload: "⬇️ MP4",
    noVideos: "Koi video nahi mili. Nayi video banayein!",
    listeningToast: "🎙️ Listening... Bolye!"
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
    tabTasks: "📋 Tasks & Problems",
    tabGallery: "🎬 Video Library",
    tabSettings: "⚙️ Settings & Quota",
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
    botWelcome: "👋 Hello! I am your <b>AUTOPILOT Futuristic Copilot</b>.<br><br>You can ask me to generate the next Series 1 episode, create a custom video, or scan and fix any system problems automatically!",
    pill1: "🔥 Series 1 Kaal-Rekha",
    pill2: "🛠️ Scan & Fix Problems",
    pill3: "📋 Task Status",
    pill4: "💡 5 Trending Ideas",
    pill1Text: "Generate the next episode of Series 1",
    pill2Text: "Check system problems and fix them",
    pill3Text: "How many tasks are completed and what is the status?",
    pill4Text: "Give me 5 viral mystery topic ideas",
    inputPlaceholder: "Type or speak an instruction in English...",
    btnApprove: "✅ Approve",
    btnPublish: "🚀 Publish YT",
    btnDownload: "⬇️ MP4",
    noVideos: "No videos found in library. Create a new video to get started!",
    listeningToast: "🎙️ Listening... Speak now!"
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
  const T = I18N[lang] || I18N.hi;
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
  const badgeT = document.getElementById('badgeTaskCount')?.textContent || '0';
  const badgeV = document.getElementById('badgeVideoCount')?.textContent || '0';
  setH('tab-tasks', `${T.tabTasks} <span class="tab-badge" id="badgeTaskCount">${badgeT}</span>`);
  setH('tab-gallery', `${T.tabGallery} <span class="tab-badge" id="badgeVideoCount">${badgeV}</span>`);
  setT('tab-settings', T.tabSettings);

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
      osc.frequency.value = freq;
      osc.type = 'sine';
      gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch(e) {}
  }
  success() {
    this.beep(880, 0.1);
    setTimeout(() => this.beep(1320, 0.15), 100);
  }
  click() {
    this.beep(520, 0.04);
  }
}
const audio = new CyberAudio();

function toggleAudio() {
  soundEnabled = !soundEnabled;
  const T = I18N[currentLang] || I18N.hi;
  document.getElementById('btnMute').textContent = soundEnabled ? T.soundOn : T.soundMuted;
}

function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.display = 'block';
  audio.beep(750, 0.08);
  setTimeout(() => { el.style.display = 'none'; }, 4000);
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

  if (tabId === 'tasks') {
    refreshTasks();
  }
}

// Data Fetching
async function load() {
  try {
    const r = await fetch('/api/data');
    D = await r.json();
    renderGallery();
    renderQuota();
    checkActiveTask(D.active_task);
  } catch (e) {
    console.error('Data fetch error:', e);
  }
}

// Check Active Task & Progress
function checkActiveTask(t) {
  const T = I18N[currentLang] || I18N.hi;
  const banner = document.getElementById('liveTaskBanner');
  const hStatus = document.getElementById('headerStatus');
  const sText = document.getElementById('statusText');

  if (t && t.status === 'running') {
    banner.style.display = 'block';
    document.getElementById('liveTaskName').textContent = t.task || T.liveTaskTitle;
    document.getElementById('liveTaskDetail').textContent = t.msg || T.liveTaskDetail;
    hStatus.className = 'status-pill busy';
    sText.textContent = T.statusBusy;
  } else {
    banner.style.display = 'none';
    hStatus.className = 'status-pill';
    sText.textContent = T.statusReady;
  }
}

// Render Video Gallery
function renderGallery() {
  if (!D) return;
  const T = I18N[currentLang] || I18N.hi;
  const list = [...(D.queue || []), ...(D.published || [])];
  const bEl = document.getElementById('badgeVideoCount');
  if (bEl) bEl.textContent = list.length;

  const grid = document.getElementById('videoGrid');
  if (!grid) return;
  if (!list.length) {
    grid.innerHTML = `<div style="color:var(--text-muted);grid-column:1/-1;text-align:center;padding:40px">${T.noVideos}</div>`;
    return;
  }

  grid.innerHTML = list.map(v => {
    const isPub = v.status === 'published';
    const isApp = v.status === 'approved';
    const videoUrl = v.video_url || (v.id ? `/media/video_${String(v.id).padStart(4, '0')}/final.mp4` : '');

    return `
      <div class="video-item">
        <div class="video-thumb-container">
          ${videoUrl ? `<video src="${videoUrl}" controls preload="metadata"></video>` : '<div style="color:#64748b;display:flex;align-items:center;justify-content:center;height:100%">No Preview</div>'}
        </div>
        <div class="video-item-body">
          <div>
            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
              <span class="series-badge" style="background:${isPub ? 'rgba(16,185,129,0.15)' : 'rgba(56,189,248,0.15)'};color:${isPub ? '#34d399' : '#38bdf8'}">
                ${esc(v.status || 'Ready')}
              </span>
              <span style="font-size:11px;color:var(--text-dim)">#${v.id}</span>
            </div>
            <div class="video-item-title">${esc(v.title || v.topic || 'Video #' + v.id)}</div>
          </div>
          <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
            ${!isPub && !isApp ? `<button class="btn btn-primary" style="padding:6px 12px;font-size:12px" onclick="act('approve', ${v.id})">${T.btnApprove}</button>` : ''}
            ${!isPub ? `<button class="btn btn-success" style="padding:6px 12px;font-size:12px" onclick="act('publish_video', ${v.id})">${T.btnPublish}</button>` : ''}
            ${videoUrl ? `<a href="${videoUrl}" download class="btn btn-ghost" style="padding:6px 12px;font-size:12px;text-decoration:none">${T.btnDownload}</a>` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Render Quota
function renderQuota() {
  if (!D || !D.quota) return;
  const qc = document.getElementById('quotaContainer');
  if (!qc) return;
  const q = D.quota;

  qc.innerHTML = Object.entries(q).map(([key, val]) => {
    const used = val.used || 0;
    const lim = val.limit || 100;
    const pct = Math.min(100, Math.round((used / lim) * 100));
    return `
      <div style="background:rgba(0,0,0,0.3);padding:14px;border-radius:12px;border:1px solid var(--border)">
        <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:6px">
          <span>${esc(key)}</span>
          <span style="color:${pct > 80 ? 'var(--red)' : 'var(--cyan)'}">${used} / ${lim}</span>
        </div>
        <div style="width:100%;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden">
          <div style="width:${pct}%;height:100%;background:${pct > 80 ? 'var(--red)' : 'var(--cyan)'};transition:width 0.3s"></div>
        </div>
      </div>
    `;
  }).join('');
}

// Tasks & Problems Dashboard Fetcher
async function refreshTasks() {
  try {
    const T = I18N[currentLang] || I18N.hi;
    const r1 = await fetch('/api/tasks/summary');
    const tData = await r1.json();
    if (tData.ok) {
      document.getElementById('metricTotalTasks').textContent = tData.counts.total;
      document.getElementById('metricCompletedTasks').textContent = tData.counts.completed;
      document.getElementById('metricFailedTasks').textContent = tData.counts.failed;
      document.getElementById('metricSuccessRate').textContent = tData.success_rate + '%';
      const bTask = document.getElementById('badgeTaskCount');
      if (bTask) bTask.textContent = tData.counts.total;

      const tb = document.getElementById('tasksTableBody');
      if (!tData.jobs || !tData.jobs.length) {
        tb.innerHTML = `<tr><td colspan="5" style="color:var(--text-muted);text-align:center">${currentLang==='en'?'No task history found.':'Koi task history nahi mili.'}</td></tr>`;
      } else {
        tb.innerHTML = tData.jobs.map(j => {
          const st = j.status;
          const isOk = st === 'completed';
          const isErr = st === 'failed';
          const badgeClass = isOk ? 'background:rgba(16,185,129,0.15);color:#34d399' : (isErr ? 'background:rgba(239,68,68,0.15);color:#f87171' : 'background:rgba(56,189,248,0.15);color:#38bdf8');
          const timeStr = j.created_ts ? j.created_ts.replace('T', ' ').slice(0, 19) : '-';

          return `
            <tr>
              <td><b>${esc(j.action || 'task')}</b></td>
              <td>${esc(j.topic || j.job_id)}</td>
              <td><span class="status-pill" style="${badgeClass}">${esc(st)}</span></td>
              <td style="color:var(--text-muted);font-family:'JetBrains Mono'">${timeStr}</td>
              <td>
                ${j.video_id ? `<button class="btn btn-ghost" style="padding:4px 8px;font-size:11px" onclick="switchNav('gallery')">▶️ Video</button>` : ''}
                ${isErr ? `<button class="btn btn-primary" style="padding:4px 8px;font-size:11px" onclick="applyFix('retry_last')">🔄 Retry</button>` : ''}
              </td>
            </tr>
          `;
        }).join('');
      }
    }

    const r2 = await fetch('/api/problems');
    const pData = await r2.json();
    const pSec = document.getElementById('problemSection');

    if (pData.ok && pData.has_problems) {
      pSec.innerHTML = pData.problems.map(p => `
        <div class="problem-card">
          <div>
            <div class="problem-title">⚠️ ${esc(p.title)}</div>
            <div class="problem-desc">${esc(p.description)}</div>
          </div>
          <button class="btn btn-primary" onclick="applyFix('${p.fix_action}')">
            🛠️ ${esc(p.fix_label || 'Auto-Fix')}
          </button>
        </div>
      `).join('');
    } else {
      pSec.innerHTML = `
        <div class="healthy-banner">
          <span style="font-size:24px">🎉</span>
          <div>
            <div style="font-weight:700;font-size:15px">${T.healthyTitle}</div>
            <div style="font-size:12px;opacity:0.9">${T.healthyDesc}</div>
          </div>
        </div>
      `;
    }
  } catch (e) {
    console.error('Error refreshing tasks:', e);
  }
}

// Generation Triggers
async function generateKaalRekha() {
  audio.click();
  const epSelect = document.getElementById('series1EpSelect');
  const ep = epSelect ? epSelect.value : '';
  toast(currentLang==='en' ? '🔥 Series 1: Kaal-Rekha Production Triggered!' : '🔥 Series 1: Kaal-Rekha Episode Generation Shuru!');
  audio.success();
  await act('generate_series', 0, { series: 'SERIES_1', episode: ep || null });
  switchNav('tasks');
}

async function generateSeries(code) {
  audio.click();
  toast(currentLang==='en' ? `🎬 ${code} Production Triggered...` : `🎬 ${code} Episode Generation Triggered...`);
  audio.success();
  await act('generate_series', 0, { series: code });
  switchNav('tasks');
}

async function generateCustomVideo() {
  audio.click();
  const topic = document.getElementById('customTopicInput').value.trim();
  const voice = document.getElementById('customVoiceSelect').value;
  if (!topic) {
    alert(currentLang==='en' ? 'Please enter a topic or select an idea chip.' : 'Kripya ek topic enter karein ya chip select karein.');
    return;
  }
  toast(currentLang==='en' ? '🚀 Video Generation Triggered!' : '🚀 Video Generation Shuru!');
  audio.success();
  await act('generate', 0, { topic, voice });
  switchNav('tasks');
}

// Action Trigger
async function act(action, id, extra = {}) {
  audio.click();
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.assign({ action, video_id: id }, extra))
    });
    const res = await r.json();
    if (res.ok) {
      toast(res.msg || 'Action successful! 🎉');
      load();
      refreshTasks();
    } else {
      toast('Error: ' + (res.error || 'Action failed'));
    }
    return res;
  } catch (e) {
    toast('Network Error: ' + e);
  }
}

// Apply Auto-Fix
async function applyFix(action) {
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
      toast(res.msg || 'Fix applied successfully! ✅');
      audio.success();
      refreshTasks();
      load();
    } else {
      toast('Fix Error: ' + (res.error || 'Could not apply fix'));
    }
  } catch (e) {
    toast('Error: ' + e);
  }
}

// Futuristic Copilot Functions
function toggleCopilot() {
  audio.click();
  const d = document.getElementById('copilotDrawer');
  d.style.display = (d.style.display === 'flex') ? 'none' : 'flex';
  if (d.style.display === 'flex') {
    document.getElementById('copilotInput').focus();
  }
}

function sendCopilot(text) {
  document.getElementById('copilotInput').value = text;
  submitCopilot();
}

async function submitCopilot() {
  const input = document.getElementById('copilotInput');
  const msg = input.value.trim();
  if (!msg) return;

  const msgs = document.getElementById('copilotMessages');
  msgs.innerHTML += `<div class="copilot-msg user">${esc(msg)}</div>`;
  input.value = '';
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
      let replyHtml = esc(res.reply).replace(/\n/g, '<br>');
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
  if (isListening && recognition) {
    recognition.stop();
    isListening = false;
    micBtn.classList.remove('listening');
    return;
  }

  try {
    recognition = new SR();
    recognition.lang = (currentLang === 'en') ? 'en-US' : 'hi-IN';
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('listening');
      const T = I18N[currentLang] || I18N.hi;
      toast(T.listeningToast);
    };
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      document.getElementById('copilotInput').value = transcript;
      isListening = false;
      micBtn.classList.remove('listening');
      submitCopilot();
    };
    recognition.onerror = () => {
      isListening = false;
      micBtn.classList.remove('listening');
    };
    recognition.onend = () => {
      isListening = false;
      micBtn.classList.remove('listening');
    };
    recognition.start();
  } catch (e) {
    console.error('Speech recognition error:', e);
  }
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

// Boot with saved language
applyLanguage(currentLang);
load();
refreshTasks();
setInterval(load, 5000);
setInterval(refreshTasks, 8000);
</script>
</body>
</html>"""


def serve(host: str = HOST, port: int = PORT, open_browser: bool = True):
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
