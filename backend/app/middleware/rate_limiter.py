"""
Rate Limiting middleware using Redis (async).
Implements sliding window rate limiting on auth and API endpoints.

Blueprint requirement: 5/min on auth brute-force, 300/min on general API.

PERFORMANCE FIX (Session 5, Feb 21 2026):
  1. Replaced synchronous redis with redis.asyncio.
  2. Converted from BaseHTTPMiddleware to pure ASGI middleware.

COOKIE MIGRATION FIX (Session Feb 24 2026):
  3. Added EXEMPT_PATHS for /auth/me (session check on every page load)
     and /auth/logout (must always work). Without this, rapid F5 refreshes
     hit the auth rate limit and cause 429 → phantom logout.
"""
import time

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings

settings = get_settings()

_redis_client = None


async def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client


async def _check_rate_limit(key, max_requests, window_seconds=60):
    try:
        r = await _get_redis()
        now = time.time()
        window_start = now - window_seconds

        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()

        request_count = results[2]
        remaining = max(0, max_requests - request_count)
        return request_count <= max_requests, remaining
    except Exception:
        # Redis down — fail open (allow request)
        return True, max_requests


# Paths exempt from ALL rate limiting.
# /auth/me = session check on every page load/F5, not abusable
# /auth/logout = must always succeed to clear session
EXEMPT_PATHS = {"/api/v1/auth/me", "/api/v1/auth/logout"}

# Auth brute-force endpoints — these get the strict auth rate limit
AUTH_BRUTE_FORCE_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"}


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path
        method = request.method

        # Skip OPTIONS (CORS preflight)
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Exempt paths — no rate limiting at all
        if path in EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return

        # Auth brute-force endpoints — strict limit
        if path in AUTH_BRUTE_FORCE_PATHS:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rl:auth:{client_ip}"
            max_requests = settings.RATE_LIMIT_AUTH
        # General API — higher limit
        elif path.startswith("/api/v1"):
            client_ip = request.client.host if request.client else "unknown"
            key = f"rl:api:{client_ip}"
            max_requests = settings.RATE_LIMIT_API
        else:
            # Non-API paths (static files, etc.) — no rate limit
            await self.app(scope, receive, send)
            return

        allowed, remaining = await _check_rate_limit(key, max_requests)

        if not allowed:
            response = Response(
                content='{"detail":"Rate limit exceeded. Max ' + str(max_requests) + ' requests per minute."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )
            await response(scope, receive, send)
            return

        # Add rate limit headers to response
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-ratelimit-limit", str(max_requests).encode()))
                headers.append((b"x-ratelimit-remaining", str(remaining).encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
