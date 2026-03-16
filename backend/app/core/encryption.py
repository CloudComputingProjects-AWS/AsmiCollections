"""
PII Encryption at Rest — AES-256-GCM
Encrypts: phone, address_line_1, address_line_2, address phone
Decrypts on SELECT, encrypts on INSERT/UPDATE.

Usage:
    from app.core.encryption import encrypt_pii, decrypt_pii
    encrypted = encrypt_pii("9876543210")
    plain = decrypt_pii(encrypted)

Key stored in AWS Secrets Manager (env: PII_ENCRYPTION_KEY).
Key must be 32 bytes, base64-encoded.
"""

import base64
import binascii
import os
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

settings = get_settings()

# Nonce size for AES-GCM
_NONCE_SIZE = 12  # 96 bits recommended for GCM


def _get_key() -> bytes:
    """Get AES-256 key from config. Returns 32 bytes."""
    key_b64 = settings.PII_ENCRYPTION_KEY
    if not key_b64:
        if settings.ENVIRONMENT == "development":
            # Deterministic key for local dev only — NOT for production
            return b"dev-only-32-byte-key-do-not-use!"
        raise ValueError(
            "PII_ENCRYPTION_KEY is not set. Cannot encrypt PII data in non-development environment."
        )
    return base64.b64decode(key_b64)


def encrypt_pii(plaintext: str | None) -> str | None:
    """Encrypt a PII string. Returns base64(nonce + ciphertext + tag)."""
    if plaintext is None or plaintext == "":
        return plaintext
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Store as: base64(nonce || ciphertext_with_tag)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_pii(encrypted: str | None) -> str | None:
    """Decrypt a PII string from base64(nonce + ciphertext + tag)."""
    if encrypted is None or encrypted == "":
        return encrypted
    try:
        key = _get_key()
        aesgcm = AESGCM(key)
        raw = base64.b64decode(encrypted)
        nonce = raw[:_NONCE_SIZE]
        ciphertext = raw[_NONCE_SIZE:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except (InvalidTag, ValueError, binascii.Error):
        # Legacy plaintext or corrupted data — return as-is
        return encrypted


def generate_encryption_key() -> str:
    """Generate a new AES-256 key. Use once, store in Secrets Manager."""
    key = os.urandom(32)
    return base64.b64encode(key).decode("ascii")
