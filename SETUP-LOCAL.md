# AUTOPILOT Local Development & Control Center Setup

This guide documents the local setup, architectural invariants, running instructions, and troubleshooting matrix for AUTOPILOT's API, User Studio, and Admin Control Center.

---

## 1. Prerequisites

- **Python**: 3.11+ (Python 3.13 tested)
- **Node.js**: v18+ (tested on Node v20/v24)
- **Database**: SQLite (built-in, WAL mode in `data/autopilot.db`) or PostgreSQL

---

## 2. Installation & Dependency Separation

The repository maintains a strict separation between video pipeline dependencies and API gateway dependencies:

```bash
# 1. Activate Virtual Environment
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

# 2. Install Pipeline Dependencies (Rendering, Video, TTS)
pip install -r requirements.txt

# 3. Install API Gateway Dependencies (FastAPI, Uvicorn, PyJWT, Pydantic)
pip install -r requirements-api.txt

# 4. Install DOM Test Suite Runner (jsdom)
npm install jsdom
```

---

## 3. Running the Server

`PYTHONPATH=.` is mandatory. The codebase uses both root-relative (`from core.db_base import DB_ENGINE`) and package-relative (`from ...services.platform_service import log_activity`) imports.

### Standard Command:
```bash
# Linux/macOS
PYTHONPATH=. python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Windows (PowerShell)
$env:PYTHONPATH="."
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Or using the automated helper script:
```bash
bash qa/start-control-center.sh
```

---

## 4. Key Endpoints & Credentials

| URL | Description | Default Credentials |
|---|---|---|
| `http://localhost:8000/` | Creator Video Studio App | Any registered creator |
| `http://localhost:8000/activity` | Creator Activity Log & Timeline | Current user session |
| `http://localhost:8000/admin/login` | Admin Control Center Login | `admin_abhay` / `admin_autopilot_2026` (alias `123456`) |
| `http://localhost:8000/admin/dashboard` | Admin Control Center SPA | Authenticated Admin |
| `http://localhost:8000/docs` | Swagger OpenAPI UI | Available in dev mode |
| `http://localhost:8000/health` | Service Health & Uptime | Public |

---

## 5. Automated Verification Gates (389 Assertions)

Run the full verification suite before and after making any modification:

```bash
# 1. Core API, Database & RBAC Sweep (208 Assertions)
python qa/.acceptance_sweep.py

# 2. Admin SPA DOM & Light Theme Sweep (145 Assertions)
node qa/.dom_smoke.js

# 3. User Studio DOM & Blocked Account Modal Sweep (36 Assertions)
node qa/.user_dom_smoke.js

# 4. Auth Telemetry & Payload Shape Probe
python qa/.probe.py

# 5. Syntax & Compilation Gates
node --check backend/app/static/admin.js
python -m compileall -q backend/app core
```

---

## 6. Architectural Invariants & Hard-Won Gotchas

1. **RBAC in the Database, Never Frontend**: Every privileged route reads `users.role` directly from the database on every request (`require_admin_db`). JWT claims are never trusted blindly for authorization.
2. **Cross-Tenant Isolation**: Accessing another user's project, video, or asset returns HTTP `404 Not Found` (never `403 Forbidden`, as 403 informs attackers that the record exists).
3. **Data Retention on Block**: Blocking an account sets `users.status = 'blocked'` and stores `block_reason`. It never deletes the user's projects, videos, or history.
4. **403 vs 401 on Frontend**:
   - `401 Unauthorized`: Session has expired or is invalid. Tokens are wiped from `localStorage`.
   - `403 Forbidden`: Account restricted/blocked. Tokens are retained in `localStorage` so user data does not look deleted, and `#blockedAccountModal` displays the admin's block reason.
5. **ApiResponse[T] & MetaInfo**: `ApiResponse.meta` strictly uses `MetaInfo` (`requestId`, `timestamp`, `total`, `page`, `limit`). Any aggregate dictionaries or extra keys (e.g., `summary`) must travel inside `data`.
6. **Relative Import Depths**: Inside `backend/app/api/v1/`, `..` resolves to `backend.app.api`. To reach `services` or `core`, three dots (`...`) are required: `from ...services.platform_service import log_activity`. Inside `services/`, sibling services are imported via `.sibling_service`.
7. **Secret Masking**: Admin views must never expose raw OAuth tokens, encrypted tokens, or JWT secrets. Credentials are shown masked (`id` + length only).
8. **Data Non-Fabrication**: If a metric or model name is not recorded in the database, the UI displays `"not recorded"` rather than fabricating values.

---

## 7. Troubleshooting Matrix

| Issue | Root Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'core'` | Server executed without root directory in Python path | Launch with `PYTHONPATH=.` prefix or run via `qa/start-control-center.sh`. |
| Port 8000 already in use / Stale server | Background uvicorn process running | Find PID (`Get-Process -Name python` or `netstat -ano \| findstr :8000`) and terminate the specific PID. |
| User 403 on every request after login | Frontend sending mismatched `X-Workspace-Id` | Ensure `index.html` only sends `X-Workspace-Id` if verified to match the user's session or tenant. |
| Blocked user logged out immediately | Frontend clearing token on 403 | In `apiFetch`, ensure 403 shows `showBlockedModal(detail)` without invoking `clearSession()`. |
| Admin /control/youtube returns HTTP 500 | `response_model` mismatched with dictionary payload | Use `ApiResponse[Dict[str, Any]]` instead of `ApiResponse[List[...]]`. |
| Missing auth telemetry rows | Swallowed exception or missing call in auth handler | Call `record(request, "auth.login_...", user_id=...)` on every branch of login. |
| DOM tests fail finding jsdom | `jsdom` not installed in workspace root | Run `npm install jsdom` in workspace root. |
