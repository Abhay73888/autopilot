# AUTOPILOT — INSTAGRAM IMPLEMENTATION PLAN
**Author:** Principal Backend & Meta Platform Integration Architect  
**Status:** In Execution  
**Target:** Production-Grade Meta Instagram Professional Publishing  
**Date:** September 2026

---

## 1. Phased Implementation Roadmap

This plan translates the 53 god-level requirements into an ordered, test-driven engineering execution checklist.

---

### Phase 1: Repository Audit & Planning (Completed)
- [x] Inspect existing backend framework, auth, database, and workers.
- [x] Inspect legacy single-tenant Instagram agent (`agents/ig_publisher.py`).
- [x] Verify current Meta Graph API v21.0 specs and constraints.
- [x] Generate `INSTAGRAM_AUDIT.md`.
- [x] Generate `INSTAGRAM_ARCHITECTURE.md`.
- [x] Generate `INSTAGRAM_IMPLEMENTATION_PLAN.md`.

---

### Phase 2: Configuration & Environment Setup
- [ ] Add Meta configuration parameters to `backend/app/core/config.py`:
  - `META_APP_ID`: str = ""
  - `META_APP_SECRET`: str = ""
  - `META_REDIRECT_URI`: str = "http://localhost:8000/api/v1/integrations/instagram/oauth/callback"
  - `META_API_VERSION`: str = "v21.0"
  - `META_GRAPH_BASE_URL`: str = "https://graph.facebook.com"
- [ ] Update `.env.example` with documented configuration blocks and instructions.
- [ ] Ensure `META_APP_SECRET` is marked sensitive and never exposed in client schemas or serialized logs.

---

### Phase 3: Database Models & Non-Destructive Migrations
- [ ] Extend `core/db_base.py` to create `platform_accounts` table in SQLite and PostgreSQL:
  - Columns: `id`, `workspace_id`, `platform`, `external_account_id`, `username`, `display_name`, `profile_image_url`, `account_type`, `status`, `encrypted_access_token`, `token_expires_at`, `scopes`, `metadata_json`, `last_synced_at`, `created_at`, `updated_at`, `disconnected_at`.
  - Constraint: `UNIQUE(workspace_id, platform, external_account_id)`.
- [ ] Extend `core/db_base.py` to create `publishing_jobs` table in SQLite and PostgreSQL:
  - Columns: `id`, `workspace_id`, `platform_account_id`, `video_id`, `status`, `caption`, `scheduled_at`, `external_media_id`, `external_container_id`, `error_code`, `error_message`, `retry_count`, `idempotency_key`, `published_at`, `created_at`, `updated_at`.
  - Constraint: `UNIQUE(idempotency_key)`.
- [ ] Implement query methods for platform accounts and publishing jobs with tenant isolation.

---

### Phase 4: OAuth 2.0 Security & State Handshake
- [ ] Implement OAuth state generation with HMAC-SHA256 signature and 10-minute TTL:
  - Payload: `{workspace_id, user_id, nonce, exp}`.
- [ ] Implement state verification ensuring caller's authenticated `workspace_id` matches state payload.
- [ ] Implement Meta authorization URL builder with required scopes (`instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`).
- [ ] Implement authorization code exchange for short-lived user token.
- [ ] Implement long-lived token exchange (`grant_type=fb_exchange_token`, 60-day lifespan).
- [ ] Implement Facebook Page inspection and Instagram Business Account resolution (`GET /me/accounts`).
- [ ] Store encrypted token via `core/security.py` `SecretVault` and register `platform_account` record.

---

### Phase 5: Meta API Client (`meta_client.py`)
- [ ] Create `backend/app/integrations/meta_client.py` encapsulating all HTTP calls to Graph API v21.0.
- [ ] Implement `create_media_container(ig_user_id, video_url, caption, share_to_feed=True)`.
- [ ] Implement `get_container_status(container_id)`.
- [ ] Implement `publish_media(ig_user_id, creation_id)`.
- [ ] Implement `get_media_permalink(media_id)`.
- [ ] Implement `get_content_publishing_limit(ig_user_id)`.
- [ ] Implement `get_media_insights(media_id)`.
- [ ] Implement rate-limit tracking via `X-App-Usage` headers.
- [ ] Implement structured error translation from Meta error payloads to `InstagramApiError` domain types.

---

### Phase 6: Provider Abstraction Layer
- [ ] Create `backend/app/publishers/base.py`: Define `PublishingProvider` abstract base class and domain models (`ValidationResult`, `ContainerStatus`, `PublishResult`).
- [ ] Create `backend/app/publishers/instagram.py`: Implement `InstagramPublisher` conforming to `PublishingProvider`.
- [ ] Create `backend/app/publishers/youtube.py`: Wrap YouTube publishing logic under `PublishingProvider`.
- [ ] Create `backend/app/publishers/mock_instagram.py`: Implement `MockInstagramProvider` supporting configurable response modes (`SUCCESS`, `RATE_LIMIT`, `TOKEN_EXPIRED`, `INVALID_MEDIA`, `PROCESSING_TIMEOUT`).

---

### Phase 7: Video Validation Engine
- [ ] Create `backend/app/services/reel_validator.py` enforcing Instagram Reel technical requirements:
  - Video exists on disk or storage.
  - Video container is MP4/MOV.
  - Video codec is H.264, audio codec is AAC.
  - Aspect ratio is 9:16 (vertical).
  - Duration is between 3s and 90s.
  - Caption length is $\le 2200$ characters.
  - File size is $\le 1$ GB.
- [ ] Return descriptive rejection reasons with guidance if validation fails.

---

### Phase 8: Publishing Service & API Endpoints
- [ ] Create `backend/app/services/publishing_service.py` to coordinate validation, deduplication, job creation, and dispatch.
- [ ] Implement API endpoints under `/api/v1/integrations/instagram/`:
  - `GET /oauth/start`: Returns authorization URL with HMAC state.
  - `GET /oauth/callback`: Validates state, exchanges token, saves account.
  - `GET /accounts`: Lists connected accounts for workspace (tokens redacted).
  - `POST /disconnect`: Disconnects account.
  - `GET /status`: Returns connection health and token status.
- [ ] Implement API endpoints under `/api/v1/instagram/`:
  - `POST /publish`: Dispatches immediate Reel publishing job.
  - `POST /schedule`: Schedules Reel for future UTC publishing.
  - `GET /jobs/{job_id}`: Retrieves job progress and status.
  - `POST /jobs/{job_id}/cancel`: Cancels pending or queued job.
  - `GET /posts`: Lists published Reels.
  - `GET /posts/{post_id}`: Retrieves post details.
  - `GET /analytics`: Retrieves Reel performance metrics.
  - `POST /sync`: Triggers manual sync of Instagram metrics.

---

### Phase 9: Background Worker & Idempotent Execution
- [ ] Implement `backend/app/workers/instagram_worker.py`:
  - Decrypts token via `SecretVault`.
  - Ensures public media URL exists via `core/hosting.py`.
  - Handles container polling loop with exponential backoff.
  - Calls `media_publish` upon `FINISHED` status.
  - Updates job status to `PUBLISHED` with `external_media_id`.
- [ ] Enforce idempotency: If `external_media_id` exists for job, return existing result without duplicate API call.
- [ ] Exponential backoff retry logic for transient errors (`network timeout`, `rate limit`, `container upload fail`).
- [ ] Halt retries immediately for permanent errors (`TOKEN_EXPIRED`, `PERMISSION_DENIED`, `MEDIA_INVALID`).
- [ ] Emergency stop enforcement: If workspace is paused, cancel or suspend publishing tasks.

---

### Phase 10: Content Scientist & Analytics Integration
- [ ] Connect Instagram post metrics (`views`, `reach`, `likes`, `comments`, `shares`, `saves`) to `agents/analyst.py`.
- [ ] Register Instagram variables into `agents/scientist.py` (hook retention vs. completion rate).

---

### Phase 11: Security & Quality Audit
- [ ] IDOR tests: Verify User A cannot access, connect, publish, or view User B's accounts or jobs.
- [ ] CSRF & State Tampering tests: Invalid/expired OAuth states rejected with `400`.
- [ ] Secret Leaks: Scan API responses and logs to ensure tokens and secrets are never returned or logged.
- [ ] Idempotency tests: Double-publish requests yield single job and single post.

---

### Phase 12: Verification & Test Coverage
- [ ] Create `backend/tests/test_instagram_integration.py` covering:
  - OAuth state generation & validation.
  - Account connect/disconnect lifecycle.
  - Reel video validation.
  - Async publish worker execution via `MockInstagramProvider`.
  - Idempotency deduplication.
  - Token expiration handling.
  - Multi-tenant boundary isolation.
- [ ] Run `python -m unittest discover -s backend/tests -v` (Must pass 100%).
- [ ] Run `python test_all.py` (Must pass 100%).
- [ ] Run `python run.py --dry-run` (Must remain 100% operational).
