# AUTOPILOT — Google OAuth Verification Pack & Legal Blueprint

This documentation package provides the required compliance materials for Google Cloud Trust & Safety review, YouTube API Services compliance, and scaling the AUTOPILOT platform past the default 10,000 unit/day quota barrier.

---

## 1. Privacy Policy (Google API Limited Use Disclosure)

**Effective Date:** September 10, 2026  
**Last Updated:** September 10, 2026  

AUTOPILOT ("we", "our", or "us") is dedicated to protecting the privacy and security of creators and organizations utilizing our autonomous media operating system.

### 1.1 Information We Collect
When you link your YouTube channel or Instagram account to AUTOPILOT, we collect:
* **Account Identity:** Channel ID, Channel Title, and email address associated with your Google / YouTube Account.
* **OAuth Credentials:** Refresh tokens and temporary access tokens required to publish content and analyze video performance on your behalf.
* **Analytics Telemetry:** Video view counts, audience retention curves, and engagement metrics fetched strictly via official YouTube Data & YouTube Analytics APIs.

### 1.2 How We Use Google User Data
We access and process your Google account data solely to:
1. Upload and schedule autonomous short-form videos (`#shorts`) created in your workspace directly to your authorized channel.
2. Retrieve video performance metrics (2-hour velocity, 24-hour retention) to calibrate your workspace's AI Content Scientist and improve script hooks.
3. Verify channel upload eligibility and quota availability.

### 1.3 Google API Services User Data Policy Compliance
**AUTOPILOT strictly complies with the Google API Services User Data Policy, including the Limited Use requirements:**
* We **NEVER** use Google user data or YouTube data for serving advertisements.
* We **NEVER** sell, transfer, or distribute your Google user data or OAuth tokens to third parties or data brokers.
* We **NEVER** use Google user data to train generalized AI/ML models without explicit, opt-in consent.
* All OAuth refresh tokens are encrypted at rest using industry-standard **AES-256-GCM** encryption (`core/security.py`) and are stored in isolated per-tenant vaults. Plaintext tokens are never logged or exposed via API responses.

### 1.4 Data Retention and Deletion
You can permanently delete your stored credentials and telemetry at any time by navigating to **Settings > Integrations > Disconnect Channel** or by calling our automated deletion endpoint:
`POST https://api.autopilot.media/api/v1/auth/delete-data`

Upon receipt of this request, all OAuth tokens, secrets, video drafts, and cached analytics are purged within 60 seconds from all production databases.

---

## 2. Terms of Service

### 2.1 Acceptance of Terms
By creating an AUTOPILOT account or linking external channels, you agree to these Terms of Service and adhere to YouTube's Terms of Service (`https://www.youtube.com/t/terms`) and Community Guidelines.

### 2.2 Autonomous Publishing & User Responsibility
AUTOPILOT provides automated AI assistance for research, voice synthesis, video rendering, and publishing. Users retain full editorial control over their channel configurations:
* Users may choose between `assisted` (human review required before upload) and `autonomous` mode.
* Users are solely responsible for ensuring content published via AUTOPILOT complies with local laws, copyright regulations, and platform community guidelines.

### 2.3 Quota and Fair Usage
AUTOPILOT manages shared GCP API quota through rate limiting and intelligent batching (`playlistItems.list` and `videos.list`). Attempts to circumvent tenant isolation, spam platform APIs, or bypass spend guardrails will result in immediate workspace termination.

---

## 3. User Data Deletion Instructions

### 3.1 Automated Self-Service via API
Users and automated platforms (e.g. Google Compliance Webhooks) can initiate immediate deletion via:

```bash
curl -X POST https://api.autopilot.media/api/v1/auth/delete-data \
  -H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
  -H "X-Workspace-Id: <WORKSPACE_ID>"
```

**Response (HTTP 200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "purged",
    "message": "All user data, Google OAuth tokens, and media assets have been permanently deleted.",
    "userId": "usr_9921",
    "workspaceId": "ws_101",
    "purgedAt": "2026-09-10T12:00:00Z"
  }
}
```

### 3.2 In-App Dashboard Deletion
1. Log into your dashboard (`http://localhost:8765` or cloud SaaS portal).
2. Go to **Settings -> Connected Channels**.
3. Click **Disconnect & Purge Data** next to your YouTube or Instagram account.
4. Confirm deletion. The system immediately revokes tokens and purges stored credentials from the AES-256-GCM vault.

---

## 4. YouTube API Quota-Extension Application Request Draft

**Subject:** YouTube Data API v3 Quota Increase Request for AUTOPILOT (Project ID: `autopilot-media-prod`)

### Application Details
* **Project Name:** AUTOPILOT Media Operating System
* **GCP Project ID:** `autopilot-media-prod`
* **Current Daily Quota:** 10,000 units/day
* **Requested Daily Quota:** 200,000 units/day
* **Primary Scope(s):**
  - `https://www.googleapis.com/auth/youtube.upload`
  - `https://www.googleapis.com/auth/youtube.readonly`
  - `https://www.googleapis.com/auth/yt-analytics.readonly`

### Business & Technical Justification
AUTOPILOT is an autonomous AI media generation platform serving independent creators and digital publishers. Our creators produce educational and narrative short-form content.

#### Quota Mathematics & Consumption Model
* **Video Upload (`videos.insert`):** Costs 1,600 units per upload.
  - At the default 10,000 units/day, the platform can only support **6 video uploads per day across all users**, making multi-user SaaS operation mathematically impossible.
* **Target Capacity:** 100 creators publishing 1 to 2 Shorts per day = 150 daily uploads.
  - 150 uploads × 1,600 units = **240,000 units/day**.
* **Quota Efficiency Measures Implemented:**
  1. **Strictly 0 `search.list` calls:** We forbid `search.list` (100 units). All channel queries use `channels.list` (1 unit) and `playlistItems.list` (1 unit).
  2. **Staggered Polling:** Analytics fetching occurs strictly in 2-hour and 24-hour windows, never continuous polling.
  3. **Local Caching:** Video IDs and channel metadata are cached with 24-hour TTLs in PostgreSQL/Redis.

---

## 5. Google Trust & Safety 2-Minute Demo Video Script

**Target Video Duration:** 1 minute 50 seconds  
**Requirements:** Recorded in 1080p+, English voiceover, URL bar clearly visible showing the Google Client ID.

### Scene 1: Introduction & App Overview (0:00 - 0:25)
* **Visual:** Browser showing the AUTOPILOT dashboard and workspace overview (`https://app.autopilot.media`).
* **Voiceover:** "Welcome to AUTOPILOT, an autonomous AI media operating system that helps creators produce and publish high-retention short-form content. In this video, we demonstrate how our platform securely connects to YouTube via Google OAuth, uploads an authorized short, and enables users to revoke access and delete all data."

### Scene 2: Initiating OAuth & Consent Screen Verification (0:25 - 0:50)
* **Visual:** User clicks "Connect YouTube Channel". The Google OAuth Consent dialog opens. The browser URL bar is zoomed in to show:
  `https://accounts.google.com/o/oauth2/v2/auth?client_id=108492048-xxxx.apps.googleusercontent.com&scope=...`
* **Voiceover:** "The user navigates to Connected Channels and clicks Connect YouTube. Notice the URL bar clearly displays our registered Google Client ID. The consent screen explicitly requests two scopes: uploading videos to your YouTube account, and viewing YouTube Analytics data to measure video retention."

### Scene 3: Token Encryption & Secure Storage (0:50 - 1:10)
* **Visual:** User approves consent. Screen redirects back to AUTOPILOT dashboard showing "Channel Connected: Crime Documentary Shorts". Quick schematic overlay showing AES-256-GCM vault encryption.
* **Voiceover:** "Upon consent, the OAuth token is transmitted directly to our secure backend and encrypted in our AES-256-GCM vault. Plaintext tokens are never stored or logged."

### Scene 4: Video Generation & Upload Dispatch (1:10 - 1:35)
* **Visual:** User queues a video. Asynchronous worker renders the short, runs automated QA validation, and dispatches the upload via `videos.insert`. Cut to YouTube Studio showing the uploaded Short in "Unlisted / Private" draft mode as configured.
* **Voiceover:** "AUTOPILOT generates the script, voice narration, and video frames. The authorized worker uploads the finished MP4 directly to the user's channel as an unlisted or scheduled Short, adhering strictly to YouTube community standards."

### Scene 5: Disconnect & Permanent Data Deletion (1:35 - 1:50)
* **Visual:** User goes back to Settings, clicks "Disconnect & Purge Data". Confirmation modal displays. Screen shows credentials deleted and channel removed.
* **Voiceover:** "Users maintain complete autonomy. By clicking Disconnect, the user immediately revokes authorization, and all stored tokens and metadata are permanently erased from our databases in compliance with Google User Data policies. Thank you for your review."
