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
    """Decodes and cryptographically validates a JWT token using Supabase or local fallback. Strictly rejects refresh tokens."""
    # 1. Try Supabase JWT secret if configured
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[ALGORITHM], options={"verify_aud": False})
            if payload and payload.get("type") == "refresh":
                return None
            return payload
        except Exception:
            pass

    # 2. Local JWT fallback
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload and payload.get("type") == "refresh":
            return None
        return payload
    except Exception:
        return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and cryptographically validates a JWT refresh token. Requires type=='refresh'."""
    # 1. Try Supabase JWT secret if configured
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[ALGORITHM], options={"verify_aud": False})
            if payload and payload.get("type") == "refresh":
                return payload
        except Exception:
            pass

    # 2. Local JWT fallback
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload and payload.get("type") == "refresh":
            return payload
        return None
    except Exception:
        return None


def hash_api_key(api_key: str) -> str:
    """Returns SHA-256 hex digest of plaintext API key."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Securely hashes password using PBKDF2-HMAC-SHA256 with 16-byte random salt."""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"pbkdf2_sha256${salt}${dk}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifies plain password against stored salt$hash in constant time."""
    if not password_hash or not plain_password:
        return False
    # Standard PBKDF2 hash verification
    if "$" in password_hash:
        try:
            parts = password_hash.split("$")
            if len(parts) == 3 and parts[0] == "pbkdf2_sha256":
                salt, expected_dk = parts[1], parts[2]
            elif len(parts) == 2:
                salt, expected_dk = parts[0], parts[1]
            else:
                return False
            actual_dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
            return hmac.compare_digest(actual_dk, expected_dk)
        except Exception:
            return False
    return False


class SecretVault:
    """AES-256-GCM Encryption Engine for OAuth refresh tokens and secrets at rest."""

    def __init__(self, key_bytes: Optional[bytes] = None):
        if key_bytes is None:
            # Check for dedicated VAULT_ENCRYPTION_KEY or derive domain-separated key from secret_key
            vault_key = settings.vault_encryption_key or os.environ.get("VAULT_ENCRYPTION_KEY")
            if vault_key:
                key_bytes = hashlib.sha256(vault_key.encode("utf-8")).digest()
            else:
                # Cryptographic domain separation so vault encryption key is decoupled from JWT signing key
                key_bytes = hashlib.sha256(f"autopilot:vault-encryption-domain:{settings.secret_key}".encode("utf-8")).digest()
        self.key = key_bytes

    def encrypt_secret(self, plaintext: str) -> str:
        """Encrypts plaintext and returns base64 string."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt_secret(self, encrypted_payload: str) -> str:
        """Decrypts base64 encoded AES-GCM ciphertext with fallback for legacy key derivation."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        raw = base64.b64decode(encrypted_payload.encode("utf-8"))
        nonce = raw[:12]
        ciphertext = raw[12:]
        try:
            aesgcm = AESGCM(self.key)
            return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception:
            # Fallback to legacy key derivation for backward compatibility
            legacy_key = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
            if legacy_key != self.key:
                aesgcm_legacy = AESGCM(legacy_key)
                return aesgcm_legacy.decrypt(nonce, ciphertext, None).decode("utf-8")
            raise


vault = SecretVault()
