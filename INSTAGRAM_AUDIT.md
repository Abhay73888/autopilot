# AUTOPILOT — INSTAGRAM REELS PUBLISHING AUDIT
**Author:** Principal Backend & Meta Platform Integration Architect  
**Version:** 1.0 (Meta Graph API v21.0 / Enterprise SaaS Core)  
**Date:** September 2026

---

## 1. Executive Summary

This document performs an exhaustive architectural and technical audit of the **AUTOPILOT** media-generation SaaS codebase to prepare for integrating **Meta Instagram Professional Publishing**.

AUTOPILOT currently has:
1. A **legacy local automation engine** (`run.py`, `agents/`, `pipeline/`, `test_all.py`) that operates autonomously with SQLite and local/cached assets.
2. A **production-grade SaaS FastAPI backend** (`backend/app/main.py`, 12 v1 routers, `core/db_base.py`, `core/security.py`, `backend/tests/`) running multi-tenant workspace isolation, credit ledgers, HMAC billing webhooks, and AES-256-GCM token encryption.
3. A **legacy single-tenant Instagram agent** (`agents/ig_publisher.py`) that demonstrates the exact Meta Graph API v21.0 3-step Reel publishing protocol, but is tightly coupled to static environment variables (`IG_LONG_LIVED_TOKEN`, `IG_BUSINESS_ACCOUNT_ID`) and synchronous execution.

Our objective is to bridge this into a **first-class, multi-tenant, asynchronous, OAuth-driven Instagram publishing system** while guaranteeing **zero disruption** to existing pipeline functionality and test suites.

---

## 2. Codebase & Infrastructure Inventory

### 2.1 Backend Framework & Architecture
- **Framework:** FastAPI (`backend/app/main.py`) mounted with lifespan handlers for database pooling and background job workers.
- **Routing Structure:** All enterprise endpoints reside under `/api/v1/`:
  - `/api/v1/auth`: JWT authentication, workspace provisioning, token rotation.
  - `/api/v1/workspaces`: Workspace configuration, autopilot mode toggle (`manual`, `assisted`, `full_autopilot`), emergency stop (`emergency_stop=True`).
  - `/api/v1/projects` & `/api/v1/scripts`: Topic ideation, script generation, and workflow orchestration.
  - `/api/v1/video`: Video generation queues, rendering dispatch, QA validation checks.
  - `/api/v1/publish`: Channel connection (`/publish/channels/connect`), channel listing (`/publish/channels`), channel deletion, and video scheduling.
  - `/api/v1/analytics`: Performance loops, YouTube analytics, Content Scientist feedback.
  - `/api/v1/billing` & `/api/v1/observability`: Atomic ledger balances, HMAC webhooks, Prometheus metrics (`/metrics`), DLQ replay.

### 2.2 Multi-Tenant Context & Security
- **Tenant Context (`TenantContext`):** Derived from verified server-side JWT (`sub` as user_id, `org_id`, `workspace_id`). Bound to request context via FastAPI dependency `get_current_tenant_context()`.
- **Database Thread Isolation (`core/db_base.py`):**
  - Thread-local context `set_current_workspace()` and `get_current_workspace()`.
  - In PostgreSQL, executes `SET LOCAL app.current_workspace_id = %s;` on checkout.
  - In SQLite, enforces tenant constraints via parameter binding and workspace foreign keys.
- **Token Security Vault (`core/security.py`):**
  - Class `SecretVault` uses **AES-256-GCM** authenticated symmetric encryption (`cryptography.hazmat.primitives.ciphers.aead.AESGCM`).
  - Secret keys derived from `TOKEN_ENCRYPTION_KEY` or fallback environment secrets.
  - Tokens are encrypted prior to database insertion and decrypted only in worker execution memory.
  - Plaintext tokens are strictly forbidden from logs, API responses, and client payloads.

### 2.3 Database Layer
- **Engine (`core/db_base.py`):** Supports PostgreSQL (`psycopg2.pool.ThreadedConnectionPool`) and SQLite fallback.
- **Existing Schemas:**
  - `organizations`: Enterprise parent entities with billing settings.
  - `workspaces`: Sub-tenants containing brand kits, autopilot preferences, and emergency stop flags.
  - `channel_credentials`: Key-value storage storing `workspace_id, platform, channel_id, channel_name, encrypted_token, token_metadata`.
  - `video_jobs`: Video rendering and processing jobs.
  - `credit_accounts` & `usage_ledger`: Double-entry atomic ledger tracking billing credits.
  - `videos`: Media assets tracked across production lifecycle.

### 2.4 Worker & Queue Architecture
- **Worker Infrastructure (`backend/app/workers/`):**
  - Celery application (`celery_app.py`) with Redis broker/backend configuration.
  - In-process fallback runner (`job_runner.py`) for environments without Redis, maintaining an async priority queue.
  - Dead Letter Queue (`DLQ`) system in `backend/app/services/job_service.py` with failed job tracking, replay capabilities, and audit logs.

### 2.5 Object Storage & Media Hosting
- **Hosting Engine (`core/hosting.py`):**
  - Implements `upload(path)` supporting Cloudflare R2 / AWS S3 presigned storage and public URLs.
  - Validates public URL reachability via HTTP HEAD requests (`verify(url)`).
  - Crucial requirement for Meta: Instagram Graph API servers do not accept raw binary payloads via multipart upload for Reels; Meta's ingest servers fetch the video directly from a publicly accessible HTTPS URL.

### 2.6 Existing Instagram Publisher (`agents/ig_publisher.py`)
- Demonstrates Meta Graph API v21.0 compliance:
  - 3-step publishing protocol: Container $\rightarrow$ Poll $\rightarrow$ Publish.
  - Quota management with rate-limiting header reconciliation (`X-App-Usage`).
  - Native error code classification (`_ig_error` mapping codes 24, 190, 200, 4, 17, 9, 2207001, 2207026, 2207042, 2207050, 2207052).
  - Limitations: Designed for single-tenant local runs; lacks OAuth 2.0 handshake, token rotation, background job queues, and multi-tenant isolation.

---

## 3. Official Meta Platform Requirements (Current 2026 / Graph API v21.0)

### 3.1 Account Prerequisites
- **Personal Accounts are NOT supported:** Meta Graph API strictly requires an **Instagram Professional Account** (either **Business** or **Creator**).
- **Facebook Page Connection:** The Instagram Professional account must be connected to a Facebook Page managed by the authenticating Meta user.
- **App Review & Permissions:**
  - `instagram_basic`: Read account profile, username, id.
  - `instagram_content_publish`: Create containers and publish Reels/posts.
  - `pages_show_list`: Enumerate Facebook Pages owned by the user.
  - `pages_read_engagement`: Access Page metadata linked to the Instagram account.
  - `business_management` (for Business accounts managed via Business Manager).

### 3.2 Meta OAuth 2.0 Flow
1. **Authorization Request:**
   ```text
   GET https://www.facebook.com/v21.0/dialog/oauth?
     client_id={META_APP_ID}&
     redirect_uri={META_REDIRECT_URI}&
     state={SECURE_ENCRYPTED_STATE}&
     scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement
   ```
2. **Authorization Code Exchange:**
   ```text
   GET https://graph.facebook.com/v21.0/oauth/access_token?
     client_id={META_APP_ID}&
     redirect_uri={META_REDIRECT_URI}&
     client_secret={META_APP_SECRET}&
     code={AUTHORIZATION_CODE}
   ```
   *Returns:* Short-lived user access token (~1-2 hours).
3. **Long-Lived Token Exchange:**
   ```text
   GET https://graph.facebook.com/v21.0/oauth/access_token?
     grant_type=fb_exchange_token&
     client_id={META_APP_ID}&
     client_secret={META_APP_SECRET}&
     fb_exchange_token={SHORT_LIVED_TOKEN}
   ```
   *Returns:* Long-lived user access token (~60 days TTL).
4. **Discover Instagram Business Account:**
   ```text
   GET https://graph.facebook.com/v21.0/me/accounts?
     fields=id,name,access_token,instagram_business_account{id,username,name,profile_picture_url}
   ```
   Extracts `instagram_business_account.id` and page-scoped tokens.

### 3.3 Reel Content Publishing Flow
1. **Step 1 — Create Container:**
   ```text
   POST https://graph.facebook.com/v21.0/{ig_user_id}/media
   Body:
     media_type=REELS
     video_url={PUBLIC_HTTPS_URL}
     caption={CAPTION_STRING}
     share_to_feed=true
     access_token={ACCESS_TOKEN}
   Response: {"id": "179..."} (creation_id)
   ```
2. **Step 2 — Poll Container Status:**
   ```text
   GET https://graph.facebook.com/v21.0/{container_id}?
     fields=status_code,status&
     access_token={ACCESS_TOKEN}
   ```
   - `IN_PROGRESS`: Keep polling with exponential backoff (e.g., 5s, 8s, 12s, 15s).
   - `FINISHED`: Container is ready to be published.
   - `ERROR`: Reject; parse error detail.
   - `EXPIRED`: Containers expire after 24 hours.
3. **Step 3 — Publish Media:**
   ```text
   POST https://graph.facebook.com/v21.0/{ig_user_id}/media_publish
   Body:
     creation_id={container_id}
     access_token={ACCESS_TOKEN}
   Response: {"id": "180..."} (external_media_id)
   ```

### 3.4 Rate Limits & Technical Constraints
- **User/App Calls:** 200 calls per hour per user+app. Monitored via `X-App-Usage` header.
- **Publishing Limit:** 100 posts per 24 hours per account. Monitored via `GET /{ig_user_id}/content_publishing_limit`.
- **Reel Format Specifications:**
  - **Container:** MP4 or MOV.
  - **Video Codec:** H.264 (Progressive scan, High Profile, 4:2:0 chroma).
  - **Audio Codec:** AAC, 48kHz sample rate, stereo.
  - **Dimensions & Aspect Ratio:** 1080x1920 (9:16 vertical ratio).
  - **Duration:** Minimum 3 seconds, Maximum 90 seconds (API strict limit).
  - **File Size:** Max 1 GB.
  - **Caption Length:** Max 2,200 characters, up to 30 hashtags.

---

## 4. Reusable vs. Required Infrastructure

| Component | Existing in Repository | Action Required |
|:---|:---|:---|
| **FastAPI Core & Routing** | Yes (`backend/app/api/v1/`) | Mount new `/integrations/instagram` and `/instagram` endpoints |
| **Multi-Tenant DB Engine** | Yes (`core/db_base.py`) | Add `platform_accounts` and `publishing_jobs` tables |
| **AES-256-GCM Vault** | Yes (`core/security.py`) | Leverage `vault.encrypt_secret()` and `vault.decrypt_secret()` |
| **Hosting & Public Storage**| Yes (`core/hosting.py`) | Generate public media URLs for Meta video ingest |
| **Legacy Instagram Logic** | Yes (`agents/ig_publisher.py`)| Extract API parameters and error mapping into modular client |
| **Provider Abstraction** | No (ad-hoc router logic) | Create `PublishingProvider` interface and concrete implementations |
| **Meta API Client** | No | Build `MetaClient` with OAuth, container, status, publish, and retry logic |
| **Async Publishing Worker** | Partial (`celery_app.py`, `job_runner.py`) | Implement `instagram_publish_worker` with idempotency and backoff |
| **Mock Meta Provider** | No | Build `MockInstagramProvider` for 100% deterministic offline tests |

---

## 5. Security & Isolation Invariants

1. **OAuth CSRF & State Tampering:** State parameters must be HMAC-SHA256 signed tokens encoding `{workspace_id, user_id, nonce, exp}` with a strict 10-minute TTL. Unsigned or expired states must result in immediate `400 Bad Request`.
2. **Tenant Boundary (IDOR):** An authenticated user from Workspace A must never connect, publish, inspect, or delete an account or publishing job belonging to Workspace B. All queries enforce `workspace_id = %s`.
3. **Zero Plaintext Secrets:** `access_token`, `client_secret`, and `authorization_code` must never be logged, printed to standard output, or transmitted in client responses.
4. **Idempotency Guarantee:** Duplicate publish clicks must yield identical job status without duplicate container creation or duplicate Instagram posts (`idempotency_key` constraint).
5. **Emergency Stop Protection:** If a workspace has `emergency_stop=True`, no new Instagram jobs may be dispatched, and pending jobs must transition to `CANCELLED`.
