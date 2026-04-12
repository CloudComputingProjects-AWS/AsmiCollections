import base64
from unittest.mock import AsyncMock, MagicMock
"""verify encryption/decryption, idempotency, and the updated phone duplicate logic."""
import pytest

from app.core import encryption
from app.services.auth_service import AuthService


def _set_test_key(monkeypatch):
    key = base64.b64encode(b"0123456789abcdef0123456789abcdef").decode("ascii")
    monkeypatch.setattr(encryption.settings, "ENVIRONMENT", "aws_dev", raising=False)
    monkeypatch.setattr(encryption.settings, "PII_ENCRYPTION_KEY", key, raising=False)


def test_encrypt_decrypt_round_trip(monkeypatch):
    _set_test_key(monkeypatch)

    plaintext = "+919876543210"
    encrypted = encryption.encrypt_pii(plaintext)

    assert encrypted != plaintext
    assert encrypted.startswith("enc:v1:")
    assert encryption.decrypt_pii(encrypted) == plaintext


def test_encrypted_text_type_is_idempotent(monkeypatch):
    _set_test_key(monkeypatch)

    pii_type = encryption.EncryptedText()
    encrypted = pii_type.process_bind_param("221B Baker Street", None)

    assert pii_type.process_bind_param(encrypted, None) == encrypted
    assert pii_type.process_result_value(encrypted, None) == "221B Baker Street"
    assert pii_type.process_result_value("legacy-plaintext", None) == "legacy-plaintext"


def test_prefixed_invalid_ciphertext_raises(monkeypatch):
    _set_test_key(monkeypatch)

    with pytest.raises(ValueError, match="could not be decrypted"):
        encryption.decrypt_pii("enc:v1:not-valid-base64")


@pytest.mark.asyncio
async def test_customer_phone_exists_compares_decrypted_values():
    result = MagicMock()
    result.scalars.return_value.all.return_value = ["+919876543210", "+911234567890"]

    db = AsyncMock()
    db.execute.return_value = result

    service = AuthService(db)

    assert await service._customer_phone_exists("+919876543210") is True
    assert await service._customer_phone_exists("+919999999999") is False
