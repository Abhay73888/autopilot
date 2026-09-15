# 🗺️ AUTOPILOT — Discovery Map (Phase 0)

## 1. System Overview & Tech Stack
- **Project**: AUTOPILOT — Autonomous 12-Agent Media Swarm & YouTube Shorts Pipeline
- **Runtime**: Python 3.10+ (Standard Library priority)
- **Web Server**: `http.server.ThreadingHTTPServer` on port 8765 / `$PORT` (Zero external web framework overhead)
- **Database**: SQLite with WAL mode (`data/autopilot.db`), connection pooling and migration guards
- **Video Engine**: FFmpeg 7+ (dynamic scene cuts, panning, audio mixing, subtitles styling)
- **Voice Engine**: Microsoft Edge Neural TTS (`edge-tts`) with multi-lingual audio synthesis
- **AI Integrations**: Google Gemini API (`core/llm.py`), Pollinations AI / Wan2.1 (`agents/videogen.py`)
- **Distribution Channels**:
  - YouTube Data API v3 (OAuth2 upload, Dual-language Closed Captions .srt tracks, comment bait)
  - Instagram Graph API (`agents/ig_publisher.py`)
  - Discord Bot & Webhooks (`core/discord_service.py`)
  - Make.com / n8n Webhook API (`/api/webhook`)

---

## 2. API Endpoints Catalog

### Authentication & User Management
| Method | Path | Purpose | Access Control |
|---|---|---|---|
| POST | `/api/auth/login` | Creator & Admin authentication | Public (Credential verification) |
| POST | `/api/auth/register` | New creator account creation | Public |
| POST | `/api/auth/google` | Google Identity token verification | Public (Google TokenInfo API) |
| GET | `/api/auth/me` | Current authenticated user profile | Authenticated / Session |
| POST | `/api/user/tour-complete` | Mark onboarding tour done in DB | Authenticated |

### Core Pipeline & Media Actions
| Method | Path | Purpose | Access Control |
|---|---|---|---|
| POST | `/api/action` | Dispatches actions: `generate`, `generate_series`, `publish_video`, `approve`, `reject`, `rerender`, `validate`, `tick`, `clear_logs` | Authenticated (Admin for publish/clear) |
| POST | `/api/webhook` | Make.com automation trigger | HMAC Secret (`X-Webhook-Secret`) |
| GET | `/api/status` | Real-time task & job status polling | Public / Make.com polling |
| GET | `/api/jobs` | List recent async execution jobs | Authenticated |
| GET | `/api/jobs/<id>` | Fetch single job status & output paths | Authenticated |
| GET | `/media/<path>` | Stream generated MP4 videos & thumbnails | Sandboxed to `output/` with Range support |

### Dashboard & Analytics
| Method | Path | Purpose | Access Control |
|---|---|---|---|
| GET | `/api/data` | Dashboard metrics, approval queue, quotas | Authenticated |
| GET | `/api/series/catalog` | All 5 series metadata & next episode num | Public / Authenticated |
| GET | `/api/tasks` | Swarm agent task summaries & history | Authenticated |
| GET | `/api/problems` | Self-healing problem detection | Authenticated |
| GET | `/api/logs` | Structured logs for specific video | Authenticated |

### AI Studio, ML & Video Editor
| Method | Path | Purpose | Access Control |
|---|---|---|---|
| POST | `/api/assistant` | AI Copilot conversational assistance | Authenticated |
| GET | `/api/assistant/quick_suggestions` | Contextual 1-click action suggestions | Authenticated |
| GET | `/api/ml/insights` | ML retention regression weights & score | Authenticated |
| POST | `/api/ml/predict` | Predict audience retention score (0-100%) | Authenticated |
| POST | `/api/ml/train` | Retrain retention model with historical metrics | Admin |
| GET | `/api/editor/videos` | List editable rendered videos | Authenticated |
| GET | `/api/editor/video/<id>` | Video timeline metadata | Authenticated |
| POST | `/api/editor/export` | Apply video edits (cut, filter, hook, speed) | Authenticated |
| POST | `/api/pipeline/fix` | Execute automated self-healing pipeline fix | Admin |
| GET | `/api/channels/status` | YouTube, Instagram, Discord & AI health | Authenticated |
| POST | `/api/channels/test` | Test channel connectivity | Authenticated |

---

## 3. Database Schema Entities
1. `videos`: Core video manifests, metadata, topics, render metrics, approval status, YouTube IDs, user isolation.
2. `users`: Multi-tenant creator accounts, credentials, role (`admin` vs `creator`), credits, tier, tour completion.
3. `workspaces`: Tenant workspace units with API keys and plan tiers.
4. `jobs`: Asynchronous background task tracking with idempotency keys and request IDs.
5. `metrics`: 2h / 24h retention, views, CTR, and watch time performance.
6. `experiments`: Multi-arm A/B tests managed by Scientist agent.
7. `learnings`: Automated viral insights extracted from performance anomalies.
8. `events`: Structured audit logbook of all system actions.
9. `discord_connections`: OAuth tokens and notification bindings.
10. `characters`: Consistent character continuity profiles across series episodes.

---

## 4. Policy Constraints & Invariants
- **AGENTS.md Policy**:
  - `selfDeclaredMadeForKids` must ALWAYS be `False`.
  - `privacyStatus` must be `"public"`.
  - YouTube comments must ALWAYS be 100% ENABLED (ON).
  - First comment (`comment_bait`) must be posted via `commentThreads.insert`.
  - Never remove or alter these constraints.
