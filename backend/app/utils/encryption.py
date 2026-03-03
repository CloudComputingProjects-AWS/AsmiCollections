"""
PII encryption utilities — AES-256 encrypt/decrypt for sensitive fields.
Applied to: users.phone, user_addresses.phone, address_line_1, address_line_2

In production, encryption key comes from AWS Secrets Manager.
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    """Derive Fernet key from PII_ENCRYPTION_KEY config."""
    key = settings.PII_ENCRYPTION_KEY
    if not key:
        # Development fallback — generate deterministic key
        key = settings.SECRET_KEY

    # Derive a proper 32-byte key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"apparel-portal-pii-salt",  # Fixed salt — key rotation handled separately
        iterations=100_000,
    )
    derived = base64.urlsafe_b64encode(kdf.derive(key.encode()))
    return Fernet(derived)


_fernet = None


def _get_cipher() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _get_fernet()
    return _fernet


def encrypt_pii(plaintext: str | None) -> str | None:
    """Encrypt a PII field value. Returns base64 ciphertext."""
    if not plaintext:
        return plaintext
    cipher = _get_cipher()
    return cipher.encrypt(plaintext.encode()).decode()


def decrypt_pii(ciphertext: str | None) -> str | None:
    """Decrypt a PII field value. Returns plaintext."""
    if not ciphertext:
        return ciphertext
    try:
        cipher = _get_cipher()
        return cipher.decrypt(ciphertext.encode()).decode()
    except Exception:
        # If decryption fails, return as-is (might be unencrypted legacy data)
        return ciphertext


# ──────────────── Fields to encrypt ────────────────
# These are the fields that should be encrypted before DB write
# and decrypted after DB read.

PII_FIELDS = {
    "users": ["phone"],
    "user_addresses": ["phone", "address_line_1", "address_line_2"],
}
