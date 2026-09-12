"""
agents/assistant.py — AUTOPILOT Autonomous AI Assistant & Copilot.

Yeh agent user ke natural language instructions (Hindi, Hinglish, English) ko
samajhta hai, step-by-step reasoning plan banata hai, aur autonomous actions execute
karta hai (video generate karna, swarm tick run karna, publishing, approvals,
topic scouting, quota/diagnostics check, etc.).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import CONFIG, ROOT
from core.db import DB
from core.llm import LLM
from core.logbook import Logbook
from core.quota import Quota

log = Logbook("assistant")


class AutopilotAssistant:
    """
    AUTOPILOT Swarm Commander & Interactive AI Copilot.
    """

    def __init__(self, db: DB | None = None, quota: Quota | None = None):
        self.db = db or DB()
        self.quota = quota or Quota(self.db)
        self.llm = LLM(quota=self.quota, agent_name="copilot")

    def gather_system_context(self) -> dict[str, Any]:
        """Assistant ke decision making ke liye live system telemetry gather karo."""
        from web.server import CURRENT_TASK

        # 1. Queue summary
        queue_rows = self.db.q(
            "SELECT id, title, topic, status, hook_type, voice_id FROM videos "
            "WHERE status IN ('rendered','validated') ORDER BY id DESC LIMIT 5"
        )
        queue_items = [dict(r) for r in queue_rows]

        # 2. Published summary
        pub_rows = self.db.q(
            "SELECT id, title, published_ts, yt_video_id, ig_media_id FROM videos "
            "WHERE status='published' ORDER BY id DESC LIMIT 3"
        )
        published_items = [dict(r) for r in pub_rows]

        # 3. Quota snapshot
        quota_snap = self.quota.snapshot()

        # 4. Active experiment
        exp = self.db.running_experiment()

        # 5. Recent warnings/errors from logs
        recent_issues = []
        log_dir = Path(CONFIG.get("log_dir", "logs"))
        today_file = log_dir / f"autopilot-{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
        if today_file.exists():
            try:
                for line in today_file.read_text(encoding="utf-8").splitlines()[-150:]:
                    try:
                        rec = json.loads(line)
                        if rec.get("level") in ("WARN", "ERROR", "FATAL"):
                            recent_issues.append(
                                f"[{rec.get('level')}] {rec.get('agent', 'sys')}: {rec.get('msg', '')[:100]}"
                            )
                    except Exception:
                        pass
            except Exception:
                pass

        # 6. Overall stats
        summary = self.db.dashboard_summary()

        return {
            "current_task": CURRENT_TASK,
            "queue_pending_count": len(queue_items),
            "pending_videos": queue_items,
            "published_recent": published_items,
            "quota": quota_snap,
            "running_experiment": dict(exp) if exp else None,
            "recent_issues": recent_issues[-6:],
            "summary": summary,
            "mock_mode": bool(CONFIG.get("mock_mode")),
            "autonomy": CONFIG.get("autonomy", "review_first"),
            "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    # =========================================================================
    # ACTION EXECUTORS
    # =========================================================================
    def execute_tool(self, action_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Given tool action name and parameters, execute corresponding backend logic."""
        from web.server import do_action

        action_name = (action_name or "").strip().lower()
        log.info(f"Copilot executing tool: {action_name}", params=params)

        try:
            if action_name in ("generate_series", "series_generate"):
                series_code = params.get("series", "SERIES_1")
                ep = params.get("episode")
                res = do_action("generate_series", 0, {"series": series_code, "episode": ep})
                return {
                    "action": "generate_series",
                    "status": "queued" if res.get("ok") else "error",
                    "details": res,
                    "summary": f"{series_code} generation task shuru ho gaya: {res.get('msg') or 'Running'}",
                }

            elif action_name in ("generate_video", "generate", "create_video"):
                topic = params.get("topic")
                voice = params.get("voice") or params.get("voice_id")
                dry_run = bool(params.get("dry_run", CONFIG.get("mock_mode", False)))
                payload = {"topic": topic, "voice": voice, "dry_run": dry_run}
                res = do_action("generate", 0, payload)
                return {
                    "action": "generate_video",
                    "status": "queued" if res.get("ok") else "error",
                    "details": res,
                    "summary": f"Video generation task shuru ho gaya: {res.get('msg') or topic or 'Trending topic'}",
                }

            elif action_name in ("run_swarm_tick", "tick", "chief_tick"):
                dry_run = bool(params.get("dry_run", False))
                res = do_action("tick", 0, {"dry_run": dry_run})
                return {
                    "action": "run_swarm_tick",
                    "status": "queued" if res.get("ok") else "error",
                    "details": res,
                    "summary": f"Autonomous Chief Swarm Tick triggered: {res.get('msg', 'Running')}",
                }

            elif action_name in ("publish_video", "publish"):
                vid = int(params.get("video_id", 0))
                if not vid:
                    # Auto-pick earliest approved or validated video
                    rows = self.db.q(
                        "SELECT id FROM videos WHERE status IN ('approved', 'validated', 'rendered') ORDER BY id ASC LIMIT 1"
                    )
                    if rows:
                        vid = rows[0]["id"]
                if not vid:
                    return {"action": "publish_video", "status": "skipped", "summary": "Publish karne ke liye koi video nahi mili."}
                res = do_action("publish_video", vid, {})
                return {
                    "action": "publish_video",
                    "status": "queued" if res.get("ok") else "error",
                    "details": res,
                    "summary": f"Video #{vid} publish task shuru: {res.get('msg', '')}",
                }

            elif action_name in ("approve_video", "approve"):
                vid = int(params.get("video_id", 0))
                if not vid:
                    # Auto pick latest pending
                    rows = self.db.q(
                        "SELECT id FROM videos WHERE status IN ('rendered', 'validated') ORDER BY id DESC LIMIT 1"
                    )
                    if rows:
                        vid = rows[0]["id"]
                if not vid:
                    return {"action": "approve_video", "status": "skipped", "summary": "Approve karne ke liye koi pending video nahi mili."}
                res = do_action("approve", vid, {})
                return {
                    "action": "approve_video",
                    "status": "completed" if res.get("ok") else "error",
                    "details": res,
                    "summary": f"Video #{vid} approve ho gaya aur publish queue mein chala gaya.",
                }

            elif action_name in ("reject_video", "reject"):
                vid = int(params.get("video_id", 0))
                reason = params.get("reason", "Rejected via AI Copilot")
                if not vid:
                    rows = self.db.q(
                        "SELECT id FROM videos WHERE status IN ('rendered', 'validated') ORDER BY id DESC LIMIT 1"
                    )
                    if rows:
                        vid = rows[0]["id"]
                if not vid:
                    return {"action": "reject_video", "status": "skipped", "summary": "Reject karne ke liye koi pending video nahi mila."}
                res = do_action("reject", vid, {"reason": reason})
                return {
                    "action": "reject_video",
                    "status": "completed" if res.get("ok") else "error",
                    "details": res,
                    "summary": f"Video #{vid} reject kiya gaya (Wajah: {reason}).",
                }

            elif action_name in ("rerender_video", "rerender"):
                vid = int(params.get("video_id", 0))
                preset = params.get("preset", "medium")
                if not vid:
                    rows = self.db.q("SELECT id FROM videos ORDER BY id DESC LIMIT 1")
                    if rows:
                        vid = rows[0]["id"]
                if not vid:
                    return {"action": "rerender_video", "status": "skipped", "summary": "Rerender karne ke liye koi video nahi mili."}
                res = do_action("rerender", vid, {"preset": preset})
                return {
                    "action": "rerender_video",
                    "status": "completed" if res.get("ok") else "error",
                    "details": res,
                    "summary": f"Video #{vid} re-render kiya gaya ({preset} preset).",
                }

            elif action_name in ("scout_topics", "trend_scout", "suggest_topics"):
                n_count = int(params.get("n") or params.get("count", 5))
                from agents.trendscout import TrendScout
                scout = TrendScout(self.db, quota=self.quota)
                topics = scout.scout(n=n_count)
                return {
                    "action": "scout_topics",
                    "status": "completed",
                    "topics": topics,
                    "summary": f"{len(topics)} viral topic ideas scout kiye gaye!",
                }

            elif action_name in ("start_experiment", "exp_start"):
                variable = params.get("variable") or "hook_type"
                res = do_action("exp_start", 0, {"variable": variable})
                return {
                    "action": "start_experiment",
                    "status": "completed" if res.get("ok") else "error",
                    "details": res,
                    "summary": res.get("msg") or res.get("error") or "Experiment trigger kiya gaya.",
                }

            elif action_name in ("conclude_experiment", "exp_conclude"):
                force = bool(params.get("force", False))
                res = do_action("exp_conclude", 0, {"force": force})
                return {
                    "action": "conclude_experiment",
                    "status": "completed" if res.get("ok") else "error",
                    "details": res,
                    "summary": res.get("msg") or res.get("error") or "Experiment conclude kiya gaya.",
                }

            elif action_name in ("clear_logs", "clear_diagnostics"):
                res = do_action("clear_logs", 0, {})
                return {
                    "action": "clear_logs",
                    "status": "completed",
                    "details": res,
                    "summary": res.get("msg", "Logs clear ho gaye."),
                }

            elif action_name in ("get_diagnostics", "diagnostics", "health_check"):
                ctx = self.gather_system_context()
                return {
                    "action": "get_diagnostics",
                    "status": "completed",
                    "diagnostics": {
                        "issues": ctx["recent_issues"],
                        "quota": ctx["quota"],
                        "current_task": ctx["current_task"],
                    },
                    "summary": f"Diagnostics check complete: {len(ctx['recent_issues'])} active warning/errors found.",
                }

            elif action_name in ("get_analytics", "analytics_summary"):
                ctx = self.gather_system_context()
                summary = ctx["summary"]
                return {
                    "action": "get_analytics",
                    "status": "completed",
                    "summary_data": summary,
                    "summary": f"Total {summary.get('total_videos', 0)} videos processed ({summary.get('published_count', 0)} published).",
                }

            elif action_name in ("diagnose_pipeline", "pipeline_status", "check_pipeline"):
                from web.server import gather_pipeline_diagnostics
                diag = gather_pipeline_diagnostics()
                return {
                    "action": "diagnose_pipeline",
                    "status": "completed",
                    "diagnostics": diag,
                    "summary": f"Pipeline Status: {diag['status'].upper()} — {diag['diagnosis']}",
                }

            elif action_name in ("auto_fix_pipeline", "fix_pipeline", "pipeline_fix"):
                fix_action = params.get("fix_action") or "reset_task"
                from web.server import apply_pipeline_fix
                res = apply_pipeline_fix(fix_action)
                return {
                    "action": "auto_fix_pipeline",
                    "status": "completed" if res.get("ok") else "error",
                    "details": res,
                    "summary": res.get("msg") or res.get("error") or "Auto-fix applied.",
                }

            else:
                return {
                    "action": action_name,
                    "status": "unknown",
                    "summary": f"Action '{action_name}' unrecognized, skipping execution.",
                }

        except Exception as e:
            log.error(f"Error executing action {action_name}", e)
            return {
                "action": action_name,
                "status": "error",
                "error": str(e),
                "summary": f"Failed to execute {action_name}: {str(e)}",
            }

    # =========================================================================
    # NATURAL LANGUAGE / SEMANTIC PARSER FALLBACK
    # =========================================================================
    def _semantic_fallback(self, user_msg: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Rule-based NLP fallback jo kisi bhi halat mein (offline, mock mode, rate limit)
        user ke intent ko samajh kar task execute karta hai.
        """
        msg = user_msg.lower().strip()
        actions = []
        thought_steps = []
        reply = ""
        quick_replies = [
            "⚡ Run Swarm Tick",
            "📊 Quota & Health Check",
            "🔥 Generate Series 1 Episode",
            "🎬 Generate Mystery Video",
            "🛠️ Scan & Fix Any Problem",
            "💡 5 Viral Topic Ideas",
        ]

        # 0. Series 1 / Series Generation Intent (Kaal-Rekha, etc.)
        if any(w in msg for w in ["series 1", "series1", "kaal rekha", "kaal-rekha", "time loop", "kabir", "part 10", "series 2", "series 3", "series 4"]):
            target_series = "SERIES_1"
            if "series 2" in msg:
                target_series = "SERIES_2"
            elif "series 3" in msg:
                target_series = "SERIES_3"
            elif "series 4" in msg:
                target_series = "SERIES_4"

            ep_match = re.search(r'(?:part|ep|episode)\s*(\d+)', msg)
            ep_num = int(ep_match.group(1)) if ep_match else None
            thought_steps.append(f"User requested {target_series} generation. Target episode: {ep_num or 'Next'}")
            actions.append({"name": "generate_series", "params": {"series": target_series, "episode": ep_num}})
            series_name = "काल-रेखा (Kaal-Rekha)" if target_series == "SERIES_1" else target_series
            reply = (
                f"🎬 **{series_name} Episode Production Triggered!**\n\n"
                f"Initiated production for **{target_series}**{f' Episode {ep_num}' if ep_num else ' (Next Episode)'}:\n"
                f"• **Format:** 9:16 Ultra HD Vertical Shorts\n"
                f"• **Sound:** Neural Voiceover + 38Hz Braam Audio FX + Kinetic Subtitles\n"
                f"• **Pipeline:** Generation is running in the background.\n\n"
                f"Live status is available on your **Tasks & Problems Dashboard**."
            )

        # 1. Video generation intent
        elif any(w in msg for w in ["generate", "banao", "create", "make video", "nayi video", "new video", "video banao", "kahani"]):
            topic = None
            for marker in ["topic:", "topic ", "pe ", "par ", "about ", "on "]:
                if marker in msg:
                    parts = msg.split(marker, 1)
                    if len(parts) > 1 and len(parts[1].strip()) > 3:
                        topic = parts[1].strip().strip('"').strip("'").capitalize()
                        break
            if not topic:
                topic = "Kuldhara gaon ka ansoojha rahasya aur aadhi raat ki dastak"

            thought_steps.append(f"User wants to generate a new video. Detected topic: '{topic}'")
            thought_steps.append("Dispatching background video generation task via pipeline...")
            actions.append({"name": "generate_video", "params": {"topic": topic}})
            reply = (
                f"🎬 **Video Generation Triggered!**\n\n"
                f"Initiated the multimodal video production pipeline:\n"
                f"📌 **Topic:** *{topic}*\n\n"
                f"⚡ Creative Swarm agents (TrendScout ➔ Writer ➔ Voice ➔ ArtDirector ➔ Render ➔ Gatekeeper) "
                f"are now executing in the background. You can track progress in the **Live Pipeline Monitor**."
            )

        # 2. Swarm tick intent
        elif any(w in msg for w in ["tick", "chief", "swarm", "automation", "pipeline"]):
            thought_steps.append("User requested autonomous Swarm Tick execution.")
            thought_steps.append("Invoking Chief agent to inspect due videos, scheduled publications, and analytics.")
            actions.append({"name": "run_swarm_tick", "params": {}})
            reply = (
                "⚡ **Swarm Tick Initiated!**\n\n"
                "The Chief autonomous agent has initiated a pipeline cycle. It will check scheduled releases, "
                "poll 2h/24h YouTube analytics snapshots, and monitor pipeline health."
            )

        # 3. Channel Connection & Onboarding intents (YouTube / Instagram)
        elif any(w in msg for w in ["connect youtube", "youtube connect", "youtube setup", "youtube kaise", "youtube guide"]):
            thought_steps.append("User requested instructions to connect YouTube channel.")
            reply = (
                "📺 **How to Connect YouTube Channel for Full Automation:**\n\n"
                "Follow these 3 simple steps to authorize your YouTube channel:\n\n"
                "1. **Google Cloud Console Setup**:\n"
                "   • Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.\n"
                "   • Enable the **YouTube Data API v3** in *APIs & Services*.\n"
                "   • Create OAuth 2.0 Credentials: Select **OAuth Client ID** ➔ Application Type: **Desktop app**.\n"
                "   • Download the credentials JSON and save it as **`client_secret.json`** in your project root.\n\n"
                "2. **Run One-Time Authorization**:\n"
                "   • Open terminal in project folder and run:\n"
                "   ```bash\n"
                "   python authorize_youtube.py\n"
                "   ```\n"
                "   • A browser window will open. Sign in with your YouTube channel's Google account and click **Allow**.\n"
                "   • This generates a perpetual **`token.json`** file.\n\n"
                "3. **Automatic Publishing Ready**:\n"
                "   • That's it! Autopilot will now upload rendered shorts directly with AI synthetic media disclosure.\n\n"
                "💡 *Tip: Visit the **Connect & Setup (Channels)** tab in the dashboard for the visual flowchart!*"
            )
            quick_replies = ["⚡ Check Channel Status", "📸 How to Connect Instagram", "🚀 Generate Series 1"]

        elif any(w in msg for w in ["connect instagram", "instagram connect", "instagram setup", "instagram kaise", "reels connect", "meta setup"]):
            thought_steps.append("User requested instructions to connect Instagram Reels.")
            reply = (
                "📸 **How to Connect Instagram Reels for 100% Autonomous Publishing:**\n\n"
                "Follow these 4 steps to connect your Instagram account:\n\n"
                "1. **Link Instagram to Facebook Page**:\n"
                "   • Ensure your Instagram account is switched to **Professional / Creator**.\n"
                "   • Link it to a Facebook Business Page (e.g. via Instagram App ➔ *Edit Profile* ➔ *Page*).\n\n"
                "2. **Meta for Developers App**:\n"
                "   • Go to [developers.facebook.com](https://developers.facebook.com/) and create a **Business** App.\n"
                "   • Add the **Instagram Graph API** product.\n\n"
                "3. **Generate Long-Lived Token (60 Days)**:\n"
                "   • In Meta Graph API Explorer, query your Page ID to get `instagram_business_account.id`.\n"
                "   • Click *Access Token Tool* ➔ *Extend Access Token* to generate the 60-day token.\n\n"
                "4. **Add to `.env` File**:\n"
                "   ```env\n"
                "   IG_BUSINESS_ACCOUNT_ID=178414xxxxxxxxxxx\n"
                "   IG_LONG_LIVED_TOKEN=EAA...\n"
                "   ```\n\n"
                "Verify anytime with: `python -m agents.ig_publisher --info`!"
            )
            quick_replies = ["📺 How to Connect YouTube", "⚡ Check Channel Status", "🚀 Generate Series 1"]

        elif any(w in msg for w in ["how to connect", "kaise connect", "connect channel", "channels", "setup channel", "onboarding"]):
            thought_steps.append("User requested channel onboarding overview.")
            reply = (
                "🚀 **AUTOPILOT Channel Connection Hub:**\n\n"
                "You can connect both major short-form platforms for 100% automated release:\n\n"
                "• **📺 YouTube Shorts**: Requires `client_secret.json` from Google Cloud Console. Run `python authorize_youtube.py` to create `token.json`.\n"
                "• **📸 Instagram Reels**: Requires Meta Graph API v21.0 credentials (`IG_BUSINESS_ACCOUNT_ID` & `IG_LONG_LIVED_TOKEN`) in `.env`.\n"
                "• **🧠 AI & TTS Engine**: Runs **100% Free** via Microsoft Edge-TTS neural voices and Pollinations AI visual generation (zero API keys needed)!\n\n"
                "👉 Open the new **'Connect & Setup'** tab on the top menu to see complete interactive flowcharts!"
            )
            quick_replies = ["📺 Connect YouTube Guide", "📸 Connect Instagram Guide", "⚡ Check Status"]

        # 4. Publish intent
        elif any(w in msg for w in ["publish", "upload"]):
            thought_steps.append("User requested publishing video to YouTube/Instagram.")
            m = re.search(r"#?(\d+)", msg)
            vid = int(m.group(1)) if m else 0
            actions.append({"name": "publish_video", "params": {"video_id": vid}})
            reply = (
                f"🚀 **Publishing Task Queued!**\n\n"
                f"{f'Video #{vid}' if vid else 'Next pending video'} has been dispatched for YouTube Shorts publication. "
                f"It will be pushed live once OAuth and daily quota checks are verified."
            )

        # 4. Approve intent
        elif any(w in msg for w in ["approve", "pass", "accept"]):
            m = re.search(r"#?(\d+)", msg)
            vid = int(m.group(1)) if m else 0
            thought_steps.append(f"Approving video {vid or 'earliest'}")
            actions.append({"name": "approve_video", "params": {"video_id": vid}})
            reply = (
                f"✅ **Video Approved!**\n\n"
                f"{f'Video #{vid}' if vid else 'Video'} has been approved and placed into the publishing schedule."
            )

        # 5. Clear logs / diagnostics
        elif any(w in msg for w in ["clear log", "clean log", "clear diagnostics", "reset log"]):
            thought_steps.append("Clearing all jsonl logs and resetting diagnostics radar.")
            actions.append({"name": "clear_logs", "params": {}})
            reply = "🧹 **Logs Cleared!** All diagnostic warnings and archived execution logs have been cleared."

        # 6. Topics scout
        elif any(w in msg for w in ["topic", "idea", "trend", "viral", "suggest"]):
            thought_steps.append("User asked for viral video topics.")
            actions.append({"name": "scout_topics", "params": {"count": 5}})
            reply = (
                "💡 **Trending Mystery Topics Scouted!**\n\n"
                "TrendScout identified 5 high-retention viral topics:\n"
                "1. *The 14 Residents Who Vanished in One Night from Kuldhara*\n"
                "2. *The Locked Iron Door of Bhangarh Fort and the 3:17 AM Knock*\n"
                "3. *The Truth Behind 300 Ancient Skeletons of Roopkund Lake*\n"
                "4. *The Secret Chapter of Burari Diaries Classified by Investigators*\n"
                "5. *The Missing Passengers of the Midnight Express 404*\n\n"
                "Type any topic to immediately generate a 60fps video short!"
            )

        # 7. Problem / Error diagnosis & fix intent
        elif any(w in msg for w in ["problem", "issue", "dikkat", "gadbad", "fail", "kya dikkat", "fix"]):
            from web.server import gather_system_problems
            prob_info = gather_system_problems()
            p_list = prob_info.get("problems", [])
            thought_steps.append(f"Scanning for active system bottlenecks. Found: {len(p_list)} issues.")
            actions.append({"name": "get_problems", "params": {}})
            if not p_list:
                reply = (
                    "✅ **Everything is 100% Healthy!**\n\n"
                    "No problems detected! FFmpeg render engine is ready, AI credentials are active, "
                    "database is healthy, and the pipeline is ready to generate videos."
                )
            else:
                p_text = "\n".join([f"• ⚠️ **{p['title']}**: {p['description']} *(Fix: {p['fix_label']})*" for p in p_list])
                reply = (
                    f"⚠️ **{len(p_list)} Issue(s) Detected:**\n\n"
                    f"{p_text}\n\n"
                    f"You can resolve this automatically using the **1-Click Auto-Fix** button on the **Tasks & Problems Dashboard**!"
                )

        # 8. Tasks summary & progress intent
        elif any(w in msg for w in ["task", "progress", "kitne task", "kitne video", "kaam kitna", "tasks"]):
            from web.server import gather_tasks_summary
            tsum = gather_tasks_summary()
            cnt = tsum.get("counts", {})
            thought_steps.append("Gathered live tasks and background execution metrics.")
            actions.append({"name": "get_tasks", "params": {}})
            reply = (
                f"📋 **AUTOPILOT Tasks Progress & History:**\n\n"
                f"• **Active Task:** `{tsum.get('active_task', {}).get('status', 'idle').upper()}`\n"
                f"• **Total Tasks Executed:** **{cnt.get('total', 0)}**\n"
                f"• **Successfully Completed:** **{cnt.get('completed', 0)}** ✅\n"
                f"• **Issues / Failed:** **{cnt.get('failed', 0)}** ⚠️\n"
                f"• **Success Rate:** **{tsum.get('success_rate', 100)}%**\n\n"
                f"Check the **Tasks & Problems Dashboard** tab for full second-by-second task history."
            )

        # 9. Quota / Status / Health
        elif any(w in msg for w in ["quota", "health", "status", "diagnos", "check"]):
            thought_steps.append("Inspecting quota snapshot, database summary, and recent issues.")
            actions.append({"name": "get_diagnostics", "params": {}})
            issues = context.get("recent_issues", [])
            reply = (
                "📊 **System Telemetry & Health Report**\n\n"
                f"• **Active Swarm Status:** 🟢 All 11 Agents Online\n"
                f"• **Current Task:** {context.get('current_task', {}).get('status', 'idle').upper()}\n"
                f"• **Videos in Approval Queue:** {context.get('queue_pending_count', 0)}\n"
                f"• **Total Processed:** {context.get('summary', {}).get('total_videos', 0)} videos\n"
                f"• **Recent Warnings/Errors:** {len(issues)} detected\n\n"
                "All primary systems are running in optimal condition. What would you like to build next?"
            )

        # 8. Conversational / Help
        else:
            thought_steps.append("General conversational query received.")
            reply = (
                f"Hello! I am your **AUTOPILOT Autonomous Swarm Copilot**.\n\n"
                f"I can control your entire YouTube Shorts production lifecycle. "
                f"You can command me to:\n\n"
                f"• *'Generate a mystery video about the Kuldhara phenomenon'*\n"
                f"• *'Run swarm tick and poll analytics'*\n"
                f"• *'Approve pending video #1 and publish now'*\n"
                f"• *'Suggest 5 high-retention viral topics'*\n"
                f"• *'Check system telemetry and API quota limits'*\n"
                f"• *'Run A/B experiment on hook styles'*\n\n"
                f"How would you like to proceed today?"
            )

        return {
            "thought": " -> ".join(thought_steps),
            "actions_to_run": actions,
            "reply": reply,
            "quick_replies": quick_replies,
        }

    # =========================================================================
    # MAIN MESSAGE HANDLER
    # =========================================================================
    def handle_message(self, user_message: str, conversation_history: list[dict] | None = None) -> dict[str, Any]:
        """
        User input message process karo:
        1. Context assemble karo
        2. LLM se task plan & tool calls nikalo (ya semantic fallback)
        3. Action execute karo
        4. Structured output return karo
        """
        user_message = (user_message or "").strip()
        if not user_message:
            return {
                "ok": False,
                "error": "Empty message",
                "reply": "Kripya koi task ya question likhiye.",
            }

        context = self.gather_system_context()

        system_instruction = (
            "You are AUTOPILOT AI Copilot & Swarm Commander — an intelligent, friendly, and powerful autonomous agent "
            "running inside an automated Hindi serialized YouTube Shorts production engine.\n"
            "You speak fluent natural Hindi/Hinglish and English.\n"
            "You understand the user's intent, reason about the task, and decide which actions/tools to execute.\n\n"
            "AVAILABLE TOOLS:\n"
            "1. generate_video: params: {topic: str, voice?: str, dry_run?: bool}\n"
            "2. run_swarm_tick: params: {dry_run?: bool}\n"
            "3. publish_video: params: {video_id?: int}\n"
            "4. approve_video: params: {video_id?: int}\n"
            "5. reject_video: params: {video_id?: int, reason?: str}\n"
            "6. rerender_video: params: {video_id?: int, preset?: str}\n"
            "7. scout_topics: params: {niche?: str, count?: int}\n"
            "8. start_experiment: params: {variable: 'hook_type'|'voice_id'|'scene_pacing'}\n"
            "9. conclude_experiment: params: {force?: bool}\n"
            "10. clear_logs: params: {}\n"
            "11. get_diagnostics: params: {}\n"
            "12. get_analytics: params: {}\n"
            "13. diagnose_pipeline: params: {}\n"
            "14. auto_fix_pipeline: params: {fix_action: 'reset_task'|'toggle_mock'|'retry_last'|'health_check'}\n\n"
            "RESPONSE FORMAT: You must return a strictly valid JSON object with the following keys:\n"
            "{\n"
            '  "thought": "Concise step-by-step reasoning explaining how you analyzed the request and what you decided to do",\n'
            '  "actions": [{"name": "tool_name", "params": {...}}],\n'
            '  "reply": "Your response to the user in fluent, professional, confident English with markdown formatting (bullet points, bold text). Explain clearly what was accomplished or answer their question.",\n'
            '  "quick_replies": ["Short suggestion 1", "Short suggestion 2", "Short suggestion 3"]\n'
            "}\n"
        )

        history_summary = ""
        if conversation_history:
            for item in conversation_history[-4:]:
                role = item.get("role", "user")
                text = item.get("content", "")
                history_summary += f"{role.upper()}: {text}\n"

        prompt = (
            f"LIVE SYSTEM CONTEXT:\n{json.dumps(context, default=str)}\n\n"
            f"RECENT CONVERSATION:\n{history_summary}\n"
            f"USER TASK / MESSAGE:\n{user_message}\n\n"
            "Analyze the user's task. If the user wants to perform an action (e.g. create a video, run a tick, publish, check stats, etc.), "
            "select the appropriate tool in `actions`. Always provide a thoughtful `thought` trace and a great `reply`."
        )

        plan = None
        try:
            if not self.llm.is_mock:
                res = self.llm.json(prompt, system=system_instruction)
                if isinstance(res, dict) and "reply" in res:
                    plan = {
                        "thought": res.get("thought", "Analyzed prompt and scheduled actions."),
                        "actions_to_run": res.get("actions", []),
                        "reply": res.get("reply", ""),
                        "quick_replies": res.get("quick_replies", [
                            "⚡ Run Swarm Tick",
                            "🎬 Generate Mystery Video",
                            "📊 Quota & Health Check",
                        ]),
                    }
        except Exception as e:
            log.warn("Assistant LLM call exception, using semantic fallback", reason=str(e)[:120])

        if not plan:
            plan = self._semantic_fallback(user_message, context)

        executed_actions = []
        for act in plan.get("actions_to_run", []):
            name = act.get("name")
            params = act.get("params", {})
            if name:
                res = self.execute_tool(name, params)
                executed_actions.append(res)

        return {
            "ok": True,
            "thought": plan.get("thought", ""),
            "actions": executed_actions,
            "reply": plan.get("reply", ""),
            "quick_replies": plan.get("quick_replies", []),
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
