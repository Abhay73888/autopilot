# AUTOPILOT — BACKEND IMPLEMENTATION PLAN

**Target Architecture:** FastAPI + Pydantic V2 + SQLAlchemy / Multi-Tenant DB Base + Redis Queue + Cloudflare R2 + Distributed Workers  
**Goal:** Build the modular, production-ready SaaS backend package in `backend/` without disrupting existing local server functionality.

---

## 1. COMPONENT ARCHITECTURE & MODULE MAP

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  <-- FastAPI Gateway with middleware & routes
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            <-- Pydantic BaseSettings with .env validation
│   │   ├── security.py          <-- JWT, AES-GCM token encryption, API keys
│   │   ├── exceptions.py        <-- Standardized exception hierarchy & handlers
│   │   └── logging.py           <-- Structured JSON logging with request_id
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py            <-- Response envelope, pagination, error schemas
│   │   ├── auth.py              <-- User, Session, Token schemas
│   │   ├── workspace.py         <-- Workspace, BrandKit, Quota schemas
│   │   ├── project.py           <-- Project, Campaign schemas
│   │   ├── content.py           <-- Ideas, Scripts, Visual plans
│   │   ├── video.py             <-- Video, Render job, QA gate schemas
│   │   ├── billing.py           <-- Plans, Credits, Usage ledger schemas
│   │   └── copilot.py           <-- Natural language action schemas
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py      <-- Tenant isolation & auth dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── workspaces.py
│   │       ├── projects.py
│   │       ├── ideas.py
│   │       ├── scripts.py
│   │       ├── videos.py
│   │       ├── jobs.py          <-- Status & SSE telemetry stream
│   │       ├── publish.py
│   │       ├── analytics.py
│   │       ├── copilot.py
│   │       ├── billing.py
│   │       └── admin.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── workspace_service.py
│   │   ├── project_service.py
│   │   ├── script_service.py
│   │   ├── video_service.py
│   │   ├── job_service.py
│   │   ├── billing_service.py
│   │   └── copilot_service.py
│   │
│   └── workers/
│       ├── __init__.py
│       └── job_runner.py        <-- Asynchronous queue consumer
│
├── tests/
│   ├── __init__.py
│   └── test_api_v1.py           <-- Automated test suite for all endpoints
│
└── requirements.txt
```

---

## 2. STEP-BY-STEP IMPLEMENTATION PLAN

### Step 1: Core Foundation & Configuration
* Implement `backend/app/core/config.py` with typed environment variables and defaults.
* Implement `backend/app/core/security.py` with JWT token verification and AES-256-GCM token encryption.
* Implement `backend/app/core/exceptions.py` with structured HTTP error envelopes (`code`, `message`, `details`, `request_id`).

### Step 2: Pydantic V2 Schemas
* Build strict typed models for all input requests, output entities, and standard responses.
* Guarantee that `user_id` and `workspace_id` are injected by dependencies, never accepted directly from request body.

### Step 3: API Gateway & Versioned Routers (`/api/v1/*`)
* Create FastAPI application with CORS, GZip, and Request ID tracing middleware.
* Create `/health`, `/health/live`, `/health/ready` endpoints.
* Wire all routers under `/api/v1/*` with full OpenAPI 3.1 documentation.

### Step 4: Service Layer & Agent Orchestrator Bridging
* Connect `backend/app/services/` to existing agents in `agents/` and pipeline in `pipeline/`.
* Connect database operations to `core/db_base.py` for multi-tenant persistence.
* Connect usage tracking to `core/billing.py` for credit deduction and cost control.

### Step 5: Verification, Automated Testing & Documentation
* Run unit and integration tests across all endpoints.
* Validate that `python -m py_compile` passes cleanly.
* Confirm that legacy local `web/server.py` continues to run without interference.
