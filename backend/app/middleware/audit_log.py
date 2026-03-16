"""
Admin Activity Log Middleware.
Automatically logs all write operations (POST/PUT/PATCH/DELETE) on admin routes.
Stores in admin_activity_logs table per V2.5 blueprint.

PERFORMANCE FIX (Session 5, Feb 21 2026):
  Converted from BaseHTTPMiddleware to pure ASGI middleware to
  eliminate run_in_threadpool + anyio.Event overhead.
"""

from uuid import UUID

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings
from app.core.database import async_session_factory
from jose import JWTError
from app.core.security import decode_token

settings = get_settings()

# Methods that indicate write operations
LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Admin route prefixes to monitor
ADMIN_PREFIXES = ["/api/v1/admin"]

# Paths excluded from audit logging (prevent recursive logging issues)
AUDIT_EXCLUDED_PATHS = ["/api/v1/admin/audit-logs/archive"]


def _extract_target(path: str) -> tuple[str, str | None]:
    """
    Extract target_type and target_id from URL path.
    e.g., /api/v1/admin/products/abc-123 -> ('product', 'abc-123')
    """
    parts = path.rstrip("/").split("/")
    target_type = "unknown"
    target_id = None
    try:
        admin_idx = parts.index("admin")
        if admin_idx + 1 < len(parts):
            target_type = parts[admin_idx + 1].rstrip("s")  # 'products' -> 'product'
        if admin_idx + 2 < len(parts):
            target_id = parts[admin_idx + 2]
    except (ValueError, IndexError):
        pass
    return target_type, target_id


def _extract_action(method: str, path: str) -> str:
    """Map HTTP method + path to a readable action."""
    parts = path.rstrip("/").split("/")
    last_segment = parts[-1] if parts else ""

    if method == "POST":
        if last_segment in ("transition", "approve", "reject", "refund"):
            return last_segment
        return "create"
    elif method == "PUT" or method == "PATCH":
        return "update"
    elif method == "DELETE":
        return "delete"
    return method.lower()


class AdminAuditLogMiddleware:
    """
    Pure ASGI middleware that logs admin write operations to admin_activity_logs table.
    Captures: admin_id, action, target_type, target_id, IP, request details.

    Uses pure ASGI protocol instead of BaseHTTPMiddleware to avoid
    the run_in_threadpool + anyio.Event overhead.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path
        method = request.method

        is_admin_route = any(path.startswith(prefix) for prefix in ADMIN_PREFIXES)
        is_excluded = any(path.startswith(ep) for ep in AUDIT_EXCLUDED_PATHS)
        should_log = is_admin_route and method in LOGGED_METHODS and not is_excluded

        if not should_log:
            await self.app(scope, receive, send)
            return

        # Track response status code to only log successful operations
        response_status = None

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 500)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        # Log after response is sent (non-blocking to user)
        if response_status is not None and response_status < 400:
            try:
                await self._log_activity(request, method, path)
            except Exception:
                # Never let logging failure break the request
                pass

    async def _log_activity(self, request: Request, method: str, path: str):
        """Insert audit log entry."""
        from app.models.models import AdminActivityLog

        # Extract admin ID from JWT
        admin_id = None
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if token:
            try:
                payload = decode_token(token)
                admin_id = payload.get("sub")
            except (JWTError, AttributeError):
                return  # Token invalid or expired — skip audit log

        if not admin_id:
            return

        target_type, target_id = _extract_target(path)
        action = _extract_action(method, path)
        ip_address = request.client.host if request.client else None

        # Parse target_id as UUID if valid
        target_uuid = None
        if target_id:
            try:
                target_uuid = UUID(target_id)
            except ValueError:
                pass

        # Use a fresh session to avoid interfering with request session
        async with async_session_factory() as session:
            log_entry = AdminActivityLog(
                admin_id=UUID(admin_id),
                action=action,
                target_type=target_type,
                target_id=target_uuid,
                details={
                    "method": method,
                    "path": path,
                    "query_params": dict(request.query_params),
                },
                ip_address=ip_address,
            )
            session.add(log_entry)
            await session.commit()
