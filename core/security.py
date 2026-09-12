r"""
core/security.py — Shared Vault & Security Utilities for AUTOPILOT.
Re-exports SecretVault and cryptographic helpers from backend.app.core.security.
"""

from backend.app.core.security import (
    ALGORITHM,
    SecretVault,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_api_key,
    vault,
)

__all__ = [
    "ALGORITHM",
    "SecretVault",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "hash_api_key",
    "vault",
]
