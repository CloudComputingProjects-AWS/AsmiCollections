from starlette.types import ASGIApp, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, enable_hsts: bool = False):
        self.app = app
        self.enable_hsts = enable_hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                existing = {key.lower() for key, _ in headers}

                def add_if_missing(name: bytes, value: bytes) -> None:
                    if name.lower() not in existing:
                        headers.append((name, value))
                        existing.add(name.lower())

                add_if_missing(b"x-content-type-options", b"nosniff")
                add_if_missing(b"x-frame-options", b"DENY")
                add_if_missing(b"referrer-policy", b"strict-origin-when-cross-origin")
                add_if_missing(
                    b"permissions-policy",
                    b"camera=(), microphone=(), geolocation=()",
                )

                # Safe API-oriented CSP. Frontend CSP should be managed at CloudFront.
                add_if_missing(
                    b"content-security-policy",
                    b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
                )

                if self.enable_hsts:
                    add_if_missing(
                        b"strict-transport-security",
                        b"max-age=31536000; includeSubDomains; preload",
                    )

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_security_headers)