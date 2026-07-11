from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

settings = get_settings()

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

def _normalize_origin(value: str) -> str | None:
    if not value:
        return None

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None

    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

def get_trusted_origins() -> set[str]:
    origins: set[str] = set()

    frontend_origin = _normalize_origin(settings.FRONTEND_URL)
    if frontend_origin:
        origins.add(frontend_origin)

    for origin in settings.CORS_ORIGINS:
        normalized = _normalize_origin(origin)
        if normalized:
            origins.add(normalized)

    return origins

async def require_trusted_origin(request: Request) -> None:
    if request.method.upper() not in WRITE_METHODS:
        return

    origin = request.headers.get("origin")
    trusted_origins = get_trusted_origins()
    if not trusted_origins:
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Trusted origins are not configured."
    )
    if not origin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin header required."
        )
    
    
    normalized_origin = _normalize_origin(origin)
    if normalized_origin not in trusted_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin not allowed."
        )