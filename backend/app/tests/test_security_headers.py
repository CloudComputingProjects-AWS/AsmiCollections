from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import SecurityHeadersMiddleware


def test_security_headers_are_added():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)

    @app.get("/health")
    def health():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]
    assert response.headers["strict-transport-security"].startswith("max-age=31536000")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_hsts_can_be_disabled_for_local_http():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=False)

    @app.get("/health")
    def health():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/health")

    assert "strict-transport-security" not in response.headers