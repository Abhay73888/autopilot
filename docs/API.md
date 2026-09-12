# AUTOPILOT — API ARCHITECTURE & SPECIFICATION (V1 REST / SSE)

This specification defines the complete HTTP/RESTful and Server-Sent Events (SSE) API contract for the AUTOPILOT Autonomous AI Media Operating System.

* **Base URL**: `https://api.autopilot.ai/api/v1` (Production) / `http://localhost:8765/api/v1` (Local Dev)
* **Auth Scheme**: Bearer Token (`Authorization: Bearer <jwt_or_api_key>`)
* **Standard Response**: JSON envelope with typed payloads and standardized error objects.

---

## 1. GLOBAL CONVENTIONS & ENVELOPE

### 1.1 Standard Success Response
```json
{
  "success": true,
  "data": {},
  "meta": {
    "requestId": "req_01HPX7Z...",
    "timestamp": "2026-09-09T15:45:00Z"
  }
}
```

### 1.2 Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_CREDITS",
    "message": "Your organization has 4 credits remaining, but this generation requires 15 credits.",
    "details": {
      "required": 15,
      "current": 4,
      "upgradeUrl": "https://autopilot.ai/billing"
    }
  },
  "meta": {
    "requestId": "req_01HPX7Z...",
    "timestamp": "2026-09-09T15:45:00Z"
  }
}
```

### 1.3 Tenant Context Header
All requests scoped to a workspace must provide the active workspace identifier:
`X-Workspace-Id: 7b2e9e8f-410a-40a2-bdfa-bcfbbce91f74`
The backend verifies that the authenticated user belongs to the organization that owns this workspace. Never pass `user_id` from the client.

---

## 2. AUTHENTICATION & IDENTITY

### `POST /auth/session`
Validates client-side OAuth/JWT tokens (from Supabase/Clerk) and initializes an application session.
* **Headers**: `Authorization: Bearer <auth_token>`
* **Response**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "usr_991823...",
      "email": "creator@autopilot.ai",
      "fullName": "Abhay Mauraya",
      "avatarUrl": "https://storage.autopilot.ai/avatars/abhay.png"
    },
    "organizations": [
      {
        "id": "org_5829...",
        "name": "Acme Media Group",
        "role": "owner",
        "workspaces": [
          { "id": "ws_101...", "name": "AI Shorts Studio", "slug": "ai-shorts" },
          { "id": "ws_102...", "name": "History Mysteries", "slug": "history-mysteries" }
        ]
      }
    ]
  }
}
```

---

## 3. WORKSPACES & BRAND KITS

### `GET /workspaces/:workspaceId`
Fetches workspace configuration, active autopilot mode, and quota limits.

### `PATCH /workspaces/:workspaceId/autopilot`
Toggles Autopilot mode or triggers Emergency Stop.
* **Request**:
```json
{
  "mode": "full_autopilot",          // "manual" | "assisted" | "full_autopilot"
  "isActive": true,
  "maxDailyRenders": 5,
  "monthlyBudgetUsd": 100.00
}
```

### `POST /workspaces/:workspaceId/emergency-stop`
Immediately halts all pending and running autonomous jobs across this workspace.
* **Response**:
```json
{
  "success": true,
  "data": {
    "message": "Emergency stop triggered. 3 jobs cancelled.",
    "cancelledJobIds": ["job_123", "job_124", "job_125"]
  }
}
```

### `GET /workspaces/:workspaceId/brand-kit`
### `PUT /workspaces/:workspaceId/brand-kit`
Updates fonts, caption animations, brand colors, voice presets, and logos.

---

## 4. PROJECTS & CAMPAIGNS

### `POST /projects`
Creates a new content campaign / channel project.
* **Request**:
```json
{
  "name": "AI Tool Reviews",
  "niche": "Artificial Intelligence & SaaS",
  "targetAudience": "Developers, founders, and creators",
  "tone": "curious_and_energetic",
  "targetDurationSeconds": 45,
  "targetPlatforms": ["youtube", "tiktok", "instagram"],
  "postingFrequencyPerWeek": 7
}
```

### `GET /projects`
Returns paginated projects for the active workspace.

---

## 5. CONTENT IDEATION & SCRIPTS

### `POST /projects/:projectId/ideas/generate`
Dispatches TrendScout & IdeaLab agents to formulate scored content opportunities.
* **Request**:
```json
{
  "count": 5,
  "focusKeywords": ["autonomous agents", "open source LLMs"],
  "curiosityTarget": 90
}
```
* **Response**:
```json
{
  "success": true,
  "data": {
    "ideas": [
      {
        "id": "idea_8932...",
        "topic": "The Hidden AI Tool That Silently Replaced 10 Software Engineers",
        "viralScore": 94,
        "trendScore": 97,
        "competitionScore": 48,
        "retentionPotential": 92,
        "recommendedHook": "Stop paying for 5 AI subscriptions. This 1 open-source tool does it all...",
        "status": "pending"
      }
    ]
  }
}
```

### `POST /projects/:projectId/scripts/generate`
Invokes the ScriptWriter agent to draft a high-retention structured short-form script.
* **Request**:
```json
{
  "ideaId": "idea_8932...",
  "style": "storytelling_fast_paced",
  "targetSeconds": 45
}
```
* **Response**:
```json
{
  "success": true,
  "data": {
    "scriptId": "scp_4192...",
    "title": "The Secret AI Tool Developers Keep Quiet About",
    "hook": "Stop paying for 5 AI subscriptions.",
    "body": "Last week, a senior developer revealed the exact setup...",
    "payoff": "The tool is called Ollama, and it runs 100% locally on your machine.",
    "cta": "Link to the GitHub repo is pinned in my bio.",
    "estimatedDurationSeconds": 42,
    "scenesBreakdown": [
      { "scene": 1, "startSec": 0, "endSec": 4, "visualPrompt": "Dramatic close-up of a code editor with matrix green code reflections", "bRollKeyword": "coding in dark" },
      { "scene": 2, "startSec": 4, "endSec": 12, "visualPrompt": "Split screen comparing expensive subscription receipts with a single terminal command" }
    ]
  }
}
```

---

## 6. VIDEO GENERATION & PIPELINE (ASYNC)

### `POST /videos/generate`
Launches the distributed video synthesis pipeline across voice, art direction, and FFmpeg workers.
* **Request**:
```json
{
  "projectId": "proj_123...",
  "scriptId": "scp_4192...",
  "voiceId": "en-US-ChristopherNeural",
  "captionPreset": "modern_creator",
  "resolution": "1080x1920",
  "fps": 30
}
```
* **Response** (HTTP 202 Accepted):
```json
{
  "success": true,
  "data": {
    "jobId": "job_ren_9921...",
    "videoId": "vid_8812...",
    "status": "queued",
    "estimatedTimeSeconds": 45,
    "streamUrl": "/api/v1/jobs/job_ren_9921.../stream"
  }
}
```

### `GET /jobs/:jobId/stream` (Server-Sent Events — Real-Time Progress)
Provides real-time pipeline telemetry to the frontend.
```text
event: progress
data: {"step": "voice_synthesis", "progress": 25, "message": "Synthesizing voiceover with Edge TTS..."}

event: progress
data: {"step": "visual_generation", "progress": 60, "message": "Rendering 6 scene keyframes..."}

event: progress
data: {"step": "ffmpeg_assembly", "progress": 85, "message": "Applying word-highlight captions and audio mixing..."}

event: completed
data: {"step": "done", "progress": 100, "videoUrl": "https://storage.autopilot.ai/workspaces/ws_101/videos/vid_8812.mp4"}
```

---

## 7. QUALITY ASSURANCE (QA)

### `GET /videos/:videoId/qa`
Returns Gatekeeper agent QA validation results.
```json
{
  "success": true,
  "data": {
    "status": "passed",
    "score": 96,
    "checks": {
      "audioLevels": { "status": "passed", "lufs": -14.2, "clipping": false },
      "subtitles": { "status": "passed", "syncDriftMs": 12, "wordsCount": 118 },
      "blackFrames": { "status": "passed", "detected": 0 },
      "aspectRatio": { "status": "passed", "value": "9:16" },
      "contentSafety": { "status": "passed", "flaggedKeywords": [] }
    }
  }
}
```

---

## 8. MULTI-PLATFORM PUBLISHING & SCHEDULING

### `POST /videos/:videoId/publish`
Publishes or schedules video across connected accounts.
* **Request**:
```json
{
  "accounts": [
    {
      "platformAccountId": "acc_yt_001...",
      "scheduledFor": "2026-09-10T18:00:00Z",
      "title": "The Secret AI Tool Developers Keep Quiet About #Shorts",
      "description": "Discover how to run local AI models completely free. #ai #coding #tech",
      "tags": ["ai", "coding", "software", "tech"]
    }
  ]
}
```

---

## 9. ANALYTICS & CONTENT SCIENTIST

### `GET /analytics/overview`
Aggregated performance dashboard metrics.
* **Query Params**: `timeframe=30d`
* **Response**:
```json
{
  "success": true,
  "data": {
    "totalViews": 12849200,
    "watchTimeMinutes": 482100,
    "subscribersGained": 38421,
    "avgRetentionPercent": 71.4,
    "topPerformingHook": "Nobody tells you this about open-source AI...",
    "bestPostingHourUtc": 17
  }
}
```

### `GET /analytics/content-scientist/recommendations`
Actionable hypotheses generated from historical performance patterns.
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "id": "rec_001...",
        "category": "hook_optimization",
        "observation": "Videos beginning with a financial/resource comparison retain 27% longer at second 3.",
        "recommendation": "Use comparison hooks for the upcoming 3 AI tool scripts.",
        "confidence": 89
      }
    ]
  }
}
```

---

## 10. AI COPILOT INTERFACE

### `POST /copilot/command`
Natural language command processor with structured action dispatch and guardrails.
* **Request**:
```json
{
  "command": "Schedule 3 mystery shorts for Friday at 6 PM"
}
```
* **Response**:
```json
{
  "success": true,
  "data": {
    "intent": "BATCH_SCHEDULE_CONTENT",
    "interpretedAction": {
      "quantity": 3,
      "niche": "mystery",
      "scheduleTime": "2026-09-11T18:00:00Z"
    },
    "requiresApproval": true,
    "estimatedCredits": 45,
    "confirmationToken": "tok_cnf_8819..."
  }
}
```

---

## 11. BILLING & USAGE LEDGER

### `GET /billing/subscription`
Current tier, quota limits, renewals, and payment provider status.

### `GET /billing/credits`
Current credit balance, lifetime usage, and real-time ledger breakdown.

### `POST /billing/checkout`
Generates a Stripe / LemonSqueezy checkout session for plan upgrade or credit top-up.

---

## 12. INSTAGRAM PROFESSIONAL PUBLISHING & OAUTH

### `GET /integrations/instagram/oauth/start`
Generates a secure Meta OAuth 2.0 authorization URL containing a cryptographically signed HMAC-SHA256 state token encoding tenant identity and a 10-minute TTL.
* **Headers**: `X-Workspace-Id: <workspace_id>`
* **Response**:
```json
{
  "success": true,
  "data": {
    "authorization_url": "https://www.facebook.com/v21.0/dialog/oauth?client_id=...&state=...",
    "state": "<b64_payload>.<hmac_signature>",
    "workspace_id": "ws_101..."
  }
}
```

### `GET /integrations/instagram/oauth/callback`
Validates OAuth state signature, exchanges authorization code for short-lived token, upgrades to 60-day long-lived token (`fb_exchange_token`), discovers connected Instagram Business/Creator accounts, and securely encrypts access tokens via AES-256-GCM.
* **Query Params**: `code=<auth_code>&state=<state>`

### `GET /integrations/instagram/accounts`
Lists all active Instagram Professional accounts connected to the workspace. Access tokens are strictly redacted.

### `POST /integrations/instagram/disconnect`
Disconnects an Instagram account from the current workspace.
* **Request**: `{"platformAccountId": "pa_..."}`

### `GET /integrations/instagram/status`
Returns connection status and health indicators for Instagram publishing.

### `POST /instagram/publish`
Queues an immediate Reel publication with idempotency key protection.
* **Request**:
```json
{
  "platformAccountId": "pa_12345...",
  "videoId": "vid_67890...",
  "caption": "Check out this AI-generated mystery story! #mystery #ai #viral",
  "shareToFeed": true,
  "idempotencyKey": "client_req_001"
}
```
* **Response**:
```json
{
  "success": true,
  "data": {
    "job_id": "job_pub_abc123...",
    "status": "queued",
    "video_id": "vid_67890...",
    "idempotency_key": "client_req_001"
  }
}
```

### `POST /instagram/schedule`
Schedules an Instagram Reel for future publication. Scheduled timestamp is normalized to UTC.
* **Request**:
```json
{
  "platformAccountId": "pa_12345...",
  "videoId": "vid_67890...",
  "caption": "Scheduled Reel #future",
  "scheduledAt": "2026-10-15T18:30:00Z",
  "timezone": "Asia/Kolkata"
}
```

### `GET /instagram/jobs/{job_id}`
Returns real-time progress, container status, and external media ID for a publishing job.

### `POST /instagram/jobs/{job_id}/cancel`
Cancels a queued or scheduled publishing job.

### `GET /instagram/posts`
Lists successfully published Instagram Reels with engagement summaries.

### `GET /instagram/analytics`
Returns aggregate reach, views, likes, comments, and saves across all published Reels.

### `POST /instagram/sync`
Triggers an on-demand synchronization of Instagram Reel performance metrics.
