# AUTOPILOT — System Architecture Specification

## 1. System Overview

**AUTOPILOT** is an **Autonomous AI Media Operating System** engineered to research, ideate, script, narrate, visually assemble, quality-validate, schedule, publish, and recursively optimize short-form video content (YouTube Shorts, Instagram Reels, TikTok) across multi-tenant creator networks.

Unlike traditional "prompt-to-video" generators, AUTOPILOT functions as an **Autonomous AI Media Workforce** operating in a continuous, metric-grounded feedback loop:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AUTOPILOT CONTINUOUS LOOP                       │
│                                                                        │
│  [ RESEARCH ] ──► [ IDEATION ] ──► [ SCRIPTING ] ──► [ AUDIO/VOICE ]   │
│        ▲                                                     │         │
│        │                                                     ▼         │
│  [ OPTIMIZATION ] ◄── [ ANALYTICS ] ◄── [ PUBLISH ] ◄── [ VIDEO QA ]   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Global Topology & Component Layout

```text
                                [ CLIENT CLIENTS / USERS ]
                                            │
                                            ▼
                               [ CLOUDFLARE CDN / EDGE ]
                                            │
                                            ▼
                           [ API GATEWAY (FastAPI / Next.js) ]
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
      [ AUTH & RBAC ]              [ RATE LIMITER ]             [ WORKSPACE CONTEXT ]
      (Clerk / Supabase)            (Upstash Redis)              (Multi-Tenant Filter)
               │                            │                            │
               └────────────────────────────┼────────────────────────────┘
                                            ▼
                             [ CORE SERVICE ORCHESTRATOR ]
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
[ POSTGRESQL (Supabase) ]          [ REDIS TASK QUEUE ]            [ CLOUDFLARE R2 ]
  - Workspaces & Users               - Research Queue                - Raw Assets
  - Content & Scripts                - Script Queue                  - Master MP4s
  - Analytics & Metrics              - Render Queue                  - Subtitles (SRT/VTT)
  - Credit Accounts                  - Publish Queue                 - Brand Kits
  - Audit Trail                      - Analytics Queue               - Presigned URLs
        │                                   │
        │                                   ▼
        │                     [ DISTRIBUTED CELERY WORKERS ]
        │         ┌─────────────────────────┼─────────────────────────┐
        │         ▼                         ▼                         ▼
        │   [ AI WORKER ]            [ RENDER WORKER ]        [ PUBLISH WORKER ]
        │  - Gemini 2.5 Flash       - FFmpeg NVENC 60fps     - YouTube Data v3 API
        │  - Claude 3.5 Sonnet      - Scene Compositor       - Instagram Graph API
        │  - ElevenLabs Neural      - Master Audio Limiter   - TikTok Content API
        │  - Groq Whisper           - Kinetic Subtitles      - OAuth Token Vault
        │         │                         │                         │
        └─────────┴─────────────────────────┴─────────────────────────┘
```

---

## 3. Provider Abstraction Layers

To prevent vendor lock-in, all external interactions are isolated behind strict interface contracts with automatic fallbacks and health monitoring.

### 3.1 LLM Service (`LLMProvider`)
```python
from abc import ABC, abstractmethod
from typing import Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, system: str | None = None, **kwargs) -> str:
        pass

    @abstractmethod
    async def generate_json(self, prompt: str, schema: dict[str, Any], system: str | None = None, **kwargs) -> dict[str, Any]:
        pass

    @abstractmethod
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pass
```
* **Primary Providers**: Google Gemini (`gemini-2.5-flash`, `gemini-2.5-pro`), Anthropic Claude (`claude-3-5-sonnet`), OpenAI (`gpt-4o`, `gpt-4o-mini`), Groq (`llama-3.3-70b-versatile`).
* **Dynamic Cost-Aware Routing**:
  * *Simple Tasks* (Trend categorizing, tag generation): Groq / Gemini Flash.
  * *High-Stakes Tasks* (Hook generation, viral narrative pacing): Claude 3.5 Sonnet / Gemini Pro.
  * *Autonomous Swarm Copilot*: Gemini 2.5 Flash with live function calling.

### 3.2 Voice Service (`TTSProvider`)
```python
class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice_id: str, speed: float = 1.0) -> tuple[bytes, list[dict]]:
        """Returns (audio_bytes, word_level_timestamps)"""
        pass

    @abstractmethod
    def calculate_cost(self, character_count: int) -> float:
        pass
```
* **Providers**: ElevenLabs (Ultra-realistic neural), OpenAI TTS (`tts-1-hd`), Edge-TTS (Zero-cost high-speed fallback), Kokoro TTS (Open-source self-hosted).
* **Word Alignment**: Automatic fallback to Groq Whisper or algorithmic phonetic duration modeling if provider lacks word timestamps.

### 3.3 Storage Service (`StorageProvider`)
```python
class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        pass

    @abstractmethod
    async def get_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
```
* **Production**: Cloudflare R2 / AWS S3 with CDN distribution and S3-compatible APIs.
* **Development**: Local disk storage mounted at `/media/` with identical interface.

### 3.4 Billing Service (`BillingProvider`)
```python
class BillingProvider(ABC):
    @abstractmethod
    async def create_customer(self, workspace_id: str, email: str) -> str:
        pass

    @abstractmethod
    async def create_checkout_session(self, customer_id: str, plan_id: str, return_url: str) -> str:
        pass

    @abstractmethod
    async def handle_webhook(self, payload: bytes, signature: str) -> dict:
        pass
```
* **Providers**: Stripe, Lemon Squeezy, Dodo Payments (optimized for global cards & India).

---

## 4. Asynchronous Job & Worker Architecture

Video rendering, audio synthesis, and AI generation **never block the web process**. All heavy workloads run as asynchronous jobs managed by distributed queues:

1. **Job Life Cycle State Machine**:
   ```text
   QUEUED ──► RUNNING ──► COMPLETED
                 │
                 ├──► FAILED ──► RETRY (Exponential Backoff, max 3)
                 │                  └──► FATAL_ERROR (Alert sent to user)
                 └──► CANCELLED (By User / Stop Autopilot)
   ```
2. **Queue Partitions**:
   * `queue:research` (Concurrency: 10, low CPU, network bound)
   * `queue:script` (Concurrency: 20, LLM bound)
   * `queue:voice` (Concurrency: 15, audio synthesis)
   * `queue:render` (Concurrency: 4 per GPU node, high compute & FFmpeg NVENC)
   * `queue:publish` (Concurrency: 5, rate-limited by YouTube/Instagram quotas)
   * `queue:analytics` (Concurrency: 10, recurring cron polling)

---

## 5. Resilience, Circuit Breakers & Failover

1. **AI Failover Chain**:
   ```text
   Primary LLM (Gemini 2.5 Flash)
         │  [RateLimit / 5xx Error]
         ▼
   Secondary LLM (Claude 3.5 Sonnet)
         │  [Timeout]
         ▼
   Fallback LLM (Groq Llama 3.3)
         │  [Total Provider Outage]
         ▼
   Deterministic Mock Fallback (System remains online)
   ```
2. **TTS Failover Chain**:
   ```text
   ElevenLabs API ──► OpenAI TTS ──► Edge-TTS Neural ──► Syllable Fallback
   ```
3. **Idempotency & Double-Run Protection**:
   * All queued jobs require a unique `idempotency_key` (e.g. `ws_{id}_job_{topic_hash}_{date}`).
   * Publishing tasks require atomic locking via Redis `SETNX` with a 300-second TTL to guarantee no duplicate uploads occur.

---

## 6. Observability, Logging & Audit Trails

Every agent action generates an immutable telemetry record:
* **Structured JSON Logs**: Written with fields `timestamp`, `level`, `workspace_id`, `agent_name`, `job_id`, `tokens_used`, `cost_usd`, `duration_ms`.
* **Central Error Tracking**: Sentry SDK integration across API gateway and Celery worker daemons.
* **Audit Ledger**: User actions (e.g. enabling Autopilot, approving videos, modifying credit balance) are stored in `audit_logs` table for SOC2 compliance readiness.
