r"""
backend/app/core/security.py — Cryptography, Token Encryption, and Authentication Security
"""

import base64
import hashlib
import hmac
import os
import time
from typing import Any, Dict, Optional
import jwt

from .config import settings

ALGORITHM = "HS256"


SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "").strip()


def create_access_token(payload: Dict[str, Any], expires_delta_seconds: int = 1800) -> str:
    """Generates a short-lived signed JWT session token (default 30 mins)."""
    to_encode = payload.copy()
    expire = time.time() + expires_delta_seconds
    to_encode.update({"exp": expire, "iat": time.time(), "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(payload: Dict[str, Any], expires_delta_seconds: int = 604800) -> str:
    """Generates a rotating refresh token (default 7 days)."""
    to_encode = payload.copy()
    expire = time.time() + expires_delta_seconds
    to_encode.update({"exp": expire, "iat": time.time(), "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and cryptographically validates a JWT token using Supabase or local fallback."""
    # 1. Try Supabase JWT secret if configured
    if SUPABASE_JWT_SECRET:
        try:
            return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[ALGORITHM], options={"verify_aud": False})
        except Exception:
            pass

    # 2. Local JWT fallback
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


def hash_api_key(api_key: str) -> str:
    """Returns SHA-256 hex digest of plaintext API key."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


class SecretVault:
    """AES-256-GCM Encryption Engine for OAuth refresh tokens and secrets at rest."""

    def __init__(self, key_bytes: Optional[bytes] = None):
        if key_bytes is None:
            # Derive 32-byte key from secret_key
            key_bytes = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
        self.key = key_bytes

    def encrypt_secret(self, plaintext: str) -> str:
        """Encrypts plaintext and returns base64 string."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt_secret(self, encrypted_payload: str) -> str:
        """Decrypts base64 encoded AES-GCM ciphertext."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(self.key)
        raw = base64.b64decode(encrypted_payload.encode("utf-8"))
        nonce = raw[:12]
        ciphertext = raw[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


vault = SecretVault()
