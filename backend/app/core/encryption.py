"""
PII Encryption at Rest — AES-256-GCM
Encrypts: phone, address_line_1, address_line_2, address phone
Decrypts on SELECT, encrypts on INSERT/UPDATE.
PII encryption helpers used by the ORM layer.
Usage:
   from app.core.encryption import encrypt_pii, decrypt_pii
    encrypted = encrypt_pii("9876543210")
    plain = decrypt_pii(encrypted)

Key stored in AWS Secrets Manager (env: PII_ENCRYPTION_KEY).
Key must be 32 bytes, base64-encoded.
Protected values are stored as:
    enc:v1:<base64(nonce || ciphertext || tag)>
"""

import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.types import TEXT, TypeDecorator

from app.core.config import get_settings

settings = get_settings()

# Nonce size for AES-GCM
_NONCE_SIZE = 12  # 96 bits recommended for GCM
_PII_PREFIX = "enc:v1:"
_DEV_FALLBACK_KEY = b"0123456789abcdef0123456789abcdef"


def _get_key() -> bytes:
    key_b64 = settings.PII_ENCRYPTION_KEY
    if not key_b64:
        if settings.ENVIRONMENT == "development":
            # Deterministic key for local dev only — NOT for production
            return _DEV_FALLBACK_KEY
        raise ValueError(
            "PII_ENCRYPTION_KEY is not set. Cannot encrypt PII data in non-development environment."
        )
    try:
        key = base64.b64decode(key_b64)
    except binascii.Error as exc:
        raise ValueError("PII_ENCRYPTION_KEY must be valid base64.") from exc

    if len(key) != 32:
        raise ValueError("PII_ENCRYPTION_KEY must decode to exactly 32 bytes.")

    return key


def is_encrypted_pii(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(_PII_PREFIX)


def encrypt_pii(plaintext: str | None) -> str | None:
    if plaintext is None or plaintext == "":
        return plaintext
    if is_encrypted_pii(plaintext):
        return plaintext

    aesgcm = AESGCM(_get_key())
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = base64.b64encode(nonce + ciphertext).decode("ascii")
    return f"{_PII_PREFIX}{payload}"


def encrypt_pii_if_needed(value: str | None) -> str | None:
    return encrypt_pii(value)


def encrypt_pii_if_needed(value: str | None) -> str | None:
    return encrypt_pii(value)


def cle(encrypted: str | None) -> str | None:
    if encrypted is None or encrypted == "":
        return encrypted
    if not is_encrypted_pii(encrypted):
        return encrypted
    try:
        aesgcm = AESGCM(_get_key())
        raw = base64.b64decode(encrypted[len(_PII_PREFIX):])
        nonce = raw[:_NONCE_SIZE]
        ciphertext = raw[_NONCE_SIZE:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except (InvalidTag, ValueError, binascii.Error) as exc:
        raise ValueError("Encrypted PII value could not be decrypted.") from exc
        # Legacy plaintext or corrupted data — return as-is

class EncryptedText(TypeDecorator):
    """SQLAlchemy field type that encrypts on write and decrypts on read."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        return encrypt_pii_if_needed(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return decrypt_pii(value)


def generate_encryption_key() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")
