# AUTOPILOT — SECURITY, PRIVACY & COMPLIANCE SPECIFICATION

Security is a foundational pillar of the AUTOPILOT platform. This document defines the threat model, cryptographic standards, tenant isolation guarantees, and content safety policies implemented across the architecture.

---

## 1. THREAT MODEL & DEFENSE-IN-DEPTH

| Attack Vector | Potential Impact | Mitigation Strategy |
|---|---|---|
| **Cross-Tenant Data Leak (IDOR)** | User A accesses User B's videos/tokens | Database RLS, mandatory server-side session workspace resolution |
| **OAuth Token Theft** | Unauthorized channel hijacking | AES-256-GCM envelope encryption at rest; ephemeral in-memory use |
| **Prompt Injection / Jailbreak** | Agent generates harmful/copyrighted media | Multi-stage input sanitization, system prompt isolation, QA Gatekeeper |
| **Denial of Service / Resource Exhaustion** | Runaway rendering costs, worker saturation | Strict per-workspace concurrency caps, credit prepayment, Redis rate limiting |
| **Spoofed Webhooks** | Fraudulent credit or subscription grants | Cryptographic HMAC-SHA256 signature verification on all incoming webhooks |

---

## 2. MULTI-TENANT ISOLATION ARCHITECTURE

```text
Incoming HTTP Request
   │
   ▼
[JWT / API Key Validation]  ──► Extracts Authenticated User ID
   │
   ▼
[Workspace Authorization Middleware]
   │ Checks: Is User an active member of Workspace's Organization?
   │ IF NO ──► HTTP 403 Forbidden (Audit Logged)
   │
   ▼
[DB Query with Tenant Binding]
   │ Sets PostgreSQL local context:
   │ SET LOCAL app.current_workspace_id = 'ws_101...';
   │
   ▼
[PostgreSQL Row Level Security (RLS)]
   │ Only rows with matching workspace_id returned
   ▼
Clean Response
```

**Golden Rule**: `workspace_id` and `user_id` supplied in request payloads or query parameters are **never** trusted. The tenant identity is derived solely from the cryptographically verified authentication context.

---

## 3. CRYPTOGRAPHIC STANDARDS & TOKEN ENCRYPTION

Platform OAuth refresh tokens (YouTube, Instagram, TikTok) are sensitive credentials. Storing them in plaintext is strictly prohibited.

### 3.1 AES-256-GCM Encryption Engine
```python
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecretVault:
    def __init__(self, master_key_hex: str):
        self.key = bytes.fromhex(master_key_hex)
        self.aesgcm = AESGCM(self.key)

    def encrypt_token(self, plaintext_token: str) -> str:
        nonce = os.urandom(12)  # 96-bit nonce
        ciphertext = self.aesgcm.encrypt(nonce, plaintext_token.encode('utf-8'), None)
        # Store as base64: nonce + ciphertext
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt_token(self, encrypted_payload: str) -> str:
        raw = base64.b64decode(encrypted_payload.encode('utf-8'))
        nonce = raw[:12]
        ciphertext = raw[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
```

---

## 4. SECURE WEBHOOK VERIFICATION

All billing events (Stripe, LemonSqueezy) and platform notifications undergo cryptographic signature validation before processing.

```python
import hmac
import hashlib

def verify_stripe_webhook(payload: bytes, signature_header: str, webhook_secret: str) -> bool:
    """
    Verifies the HMAC-SHA256 signature provided by the payment gateway
    to prevent replay and spoofing attacks.
    """
    elements = dict(item.strip().split("=") for item in signature_header.split(","))
    timestamp = elements.get("t")
    expected_sig = elements.get("v1")

    if not timestamp or not expected_sig:
        return False

    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    computed_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_sig, expected_sig)
```

---

## 5. RATE LIMITING & ABUSE PREVENTION

Rate limits are enforced at the API gateway layer using a **Redis Leaky Bucket** algorithm:

* **Authenticated API**: 120 requests/minute per workspace.
* **Autonomous Video Render Dispatches**: Controlled by subscription tier concurrency:
  - Starter: Max 1 concurrent render
  - Pro: Max 3 concurrent renders
  - Agency: Max 8 concurrent renders
* **Public Endpoints (`/auth/*`)**: 10 requests/minute per IP address.

---

## 6. CONTENT SAFETY, MODERATION & COMPLIANCE

AUTOPILOT enforces strict content guardrails to prevent copyright infringement, harmful content, and platform bans:

1. **System Prompt Moderation**: All LLM generation prompts forbid hate speech, defamatory claims, sexual content, and copyrighted trademarks.
2. **Audio Volume Normalization**: Gatekeeper guarantees compliance with broadcast standards (-14 LUFS) to avoid sudden ear-damaging volume spikes.
3. **Voice Cloning Consent Verification**: User-supplied audio for custom voice training requires cryptographic consent acknowledgement and verification against public voice sample databases.
4. **Emergency Stop Circuit Breaker**: If an anomaly is detected or the user clicks `Emergency Stop`, all pending queue items are instantly evicted, workers are signalled `SIGTERM`, and platform publishing tokens are temporarily locked.
