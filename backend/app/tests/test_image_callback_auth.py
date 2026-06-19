import hashlib
import hmac
import time

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import admin_images


TEST_SECRET = "test-image-callback-secret"


def _sign(body: bytes, timestamp: str, secret: str = TEST_SECRET) -> str:
    signed_payload = timestamp.encode("utf-8") + b"." + body
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


def test_valid_signature_is_accepted(monkeypatch):
    monkeypatch.setattr(admin_images.settings, "IMAGE_CALLBACK_SECRET", TEST_SECRET, raising=False)

    body = b'{"image_id":"123","status":"completed"}'
    timestamp = str(int(time.time()))
    signature = _sign(body, timestamp)

    admin_images._verify_image_callback_signature(
        request_body=body,
        timestamp=timestamp,
        signature=signature,
    )


def test_missing_signature_is_rejected(monkeypatch):
    monkeypatch.setattr(admin_images.settings, "IMAGE_CALLBACK_SECRET", TEST_SECRET, raising=False)

    with pytest.raises(HTTPException) as exc:
        admin_images._verify_image_callback_signature(
            request_body=b"{}",
            timestamp=str(int(time.time())),
            signature=None,
        )

    assert exc.value.status_code == 401


def test_wrong_signature_is_rejected(monkeypatch):
    monkeypatch.setattr(admin_images.settings, "IMAGE_CALLBACK_SECRET", TEST_SECRET, raising=False)

    with pytest.raises(HTTPException) as exc:
        admin_images._verify_image_callback_signature(
            request_body=b"{}",
            timestamp=str(int(time.time())),
            signature="sha256=wrong",
        )

    assert exc.value.status_code == 401


def test_expired_timestamp_is_rejected(monkeypatch):
    monkeypatch.setattr(admin_images.settings, "IMAGE_CALLBACK_SECRET", TEST_SECRET, raising=False)

    body = b"{}"
    old_timestamp = str(int(time.time()) - 600)
    signature = _sign(body, old_timestamp)

    with pytest.raises(HTTPException) as exc:
        admin_images._verify_image_callback_signature(
            request_body=body,
            timestamp=old_timestamp,
            signature=signature,
        )

    assert exc.value.status_code == 401


def test_missing_secret_is_server_error(monkeypatch):
    monkeypatch.setattr(admin_images.settings, "IMAGE_CALLBACK_SECRET", "", raising=False)

    with pytest.raises(HTTPException) as exc:
        admin_images._verify_image_callback_signature(
            request_body=b"{}",
            timestamp=str(int(time.time())),
            signature="sha256=anything",
        )

    assert exc.value.status_code == 500