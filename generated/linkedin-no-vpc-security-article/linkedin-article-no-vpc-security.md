# Securing a Serverless E-Commerce Platform Without VPC: A Cost-Conscious AWS Security Journey

![Header: Securing e-commerce without VPC](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/01-hero-no-vpc-security.png)

## Executive Summary

In our e-commerce application, we made a deliberate architecture decision:

**The backend Lambda is not attached to a VPC.**

This was not because security was ignored. It was a cost and simplicity decision. For a lean serverless e-commerce platform, adding VPC networking can introduce private subnets, route tables, security groups, and, in many outbound internet designs, NAT Gateway cost. AWS documents NAT Gateway pricing as hourly plus data processing charges, so avoiding unnecessary NAT dependency can matter when the architecture does not truly need private subnets.

The important lesson is this:

**No VPC does not mean no security. It means security must be placed at the right layers.**

For this application, we moved protection to:

- CloudFront as CDN and edge front door
- CloudFront WAF rate-based rule in Block mode
- API Gateway throttling before Lambda invocation
- HMAC authentication for the image processor callback
- App-level security headers in FastAPI
- Payment provider signature verification
- SSL database connectivity and PII encryption
- Production secret management plan using AWS Secrets Manager and AWS Systems Manager Parameter Store

This article explains the risk, the impact, and the implementation in plain language.

## The Architecture Decision

The application is a serverless e-commerce platform:

- Frontend: CloudFront CDN + S3
- Backend: FastAPI running on AWS Lambda
- API entry: CloudFront/API Gateway
- Image processing: separate image processor Lambda
- Database: managed PostgreSQL
- Payments: Razorpay and Stripe integrations

The backend Lambda remains outside a VPC for development and cost-conscious operation.

![No VPC decision map](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/06-no-vpc-decision-map.png)

The decision created one clear responsibility:

**Every public entry point must be intentionally protected.**

That is what we fixed and verified.

## Why CloudFront Matters Here

We implemented CloudFront not only as a CDN, but also as the first security edge in front of the application.

For a normal reader, think of CloudFront as a global reception desk. Customers reach a nearby CloudFront edge location first. Only traffic that passes the edge rules continues toward API Gateway and Lambda.

![CloudFront edge security](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/09-cloudfront-edge-security.png)

CloudFront provides several benefits in this no-VPC design:

| CloudFront Benefit | Why It Matters |
|---|---|
| CDN caching | Static assets are served from edge locations, reducing load on origin infrastructure |
| Edge location front door | Users connect to AWS edge locations before origin services |
| WAF integration | AWS WAF can inspect and block traffic before it reaches the backend |
| DDoS resiliency | CloudFront works with AWS edge capacity and AWS Shield protections |
| TLS at edge | HTTPS viewer connections are handled at the CloudFront edge |
| Response header policies | CloudFront can add or remove security headers at the edge when configured |

In our current implementation, CloudFront is the CDN and WAF attachment point. FastAPI also adds its own security headers so API protection does not depend only on edge behavior.

## Security Concerns Without VPC

The goal was not to ask, "Is VPC enabled?"

The better question was:

**If the app is public and serverless, what can reach it, what can lie to it, and what can increase cost?**

![Risk matrix](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/02-risk-matrix.png)

We focused on five concerns:

1. Public API abuse
2. Image processor callback trust
3. AWS-side throttling and WAF visibility
4. Secrets stored in Lambda environment variables
5. Browser and API response hardening

## 1. Public API Abuse

### What Was The Risk?

An e-commerce API must be public. Customers need to browse products, log in, add items to cart, and place orders.

The risk is not that the API is public. The risk is uncontrolled public traffic.

Without VPC, attackers, bots, crawlers, or broken clients can still reach public endpoints. If traffic is not controlled before Lambda, it can cause:

- unnecessary Lambda invocations
- higher cost
- login brute-force attempts
- scraping
- noisy logs
- poor customer experience during spikes

### What We Implemented

Rate limiting is implemented through AWS-managed controls:

- **API Gateway stage throttling**
- **CloudFront WAF rate-based rule in Block mode**

Verified API Gateway throttling:

```text
API Gateway API: 9amq4q9qa4
Stage: $default
Burst: 100
Rate: 500.0
```

Verified CloudFront WAF:

```text
Distribution: E32QTT8QPXCW64
Rule: AWS-RateBasedRule-IP-1000-CreatedByCloudFront
Action: Block
```

![Rate limiting and WAF flow](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/07-rate-limiting-waf-flow.png)

### How This Helps Without VPC

The traffic path now looks like this:

```text
Internet -> CloudFront WAF -> API Gateway throttling -> FastAPI Lambda
```

This is important because the backend Lambda should not be the first place abusive traffic is controlled. The edge and API layer should absorb that responsibility.

The result:

- abusive IPs can be blocked at CloudFront WAF
- sudden bursts can be throttled by API Gateway
- Lambda receives fewer unwanted requests
- cost exposure is reduced before compute is invoked

## 2. Image Processor Callback Was Unauthenticated

### What Is The Image Callback?

The image callback is an internal "work completed" message.

In plain language:

1. An admin uploads a product image.
2. The backend creates a pending image record and returns a pre-signed S3 upload URL.
3. The image processor Lambda creates optimized WebP image variants.
4. The image processor Lambda calls the backend and says, "Processing is complete. Here are the image URLs."
5. The backend updates the product image record in the database.

The callback endpoint is:

```text
POST /api/v1/admin/images/callback
```

### Why Was It Unsafe?

Before the fix, the backend accepted the callback without cryptographic proof that it came from the image processor Lambda.

That means if an attacker discovered the endpoint, they could try to send a fake "image completed" message.

Possible impact:

- product image records could be marked completed incorrectly
- incorrect image URLs could be stored
- failed image processing could be hidden by fake success
- product data integrity could be damaged

VPC could make this kind of callback private at the network layer. Since we intentionally avoided VPC, we secured it at the application layer.

### What We Implemented

We implemented HMAC authentication.

HMAC authentication is a way for two systems that share a secret key to prove a message is genuine by attaching a cryptographic signature that attackers cannot recreate without that secret.

The image processor Lambda signs the callback body using `IMAGE_CALLBACK_SECRET`. The backend recalculates the same signature and accepts the callback only if the signatures match.

![HMAC image callback flow](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/04-hmac-callback-flow.png)

Image processor signing code:

```python
# C:\Ashmiwebportal\backend\aws\lambda\image-processor\lambda_function.py

IMAGE_CALLBACK_SECRET = os.environ.get("IMAGE_CALLBACK_SECRET")

def _post_callback(data: dict) -> None:
    if not IMAGE_CALLBACK_SECRET:
        raise RuntimeError("IMAGE_CALLBACK_SECRET is not configured")

    body = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    timestamp = str(int(time.time()))
    signed_payload = timestamp.encode("utf-8") + b"." + body

    signature = hmac.new(
        IMAGE_CALLBACK_SECRET.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Ashmi-Timestamp": timestamp,
        "X-Ashmi-Signature": f"sha256={signature}",
    }
```

Backend verification code:

```python
# C:\Ashmiwebportal\backend\app\api\v1\endpoints\admin_images.py

def _verify_image_callback_signature(
    request_body: bytes,
    timestamp: str | None,
    signature: str | None,
) -> None:
    if not settings.IMAGE_CALLBACK_SECRET:
        raise HTTPException(status_code=500, detail="Image callback secret not configured")

    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="Missing callback signature")

    ts = int(timestamp)
    now = int(time.time())

    if abs(now - ts) > 300:
        raise HTTPException(status_code=401, detail="Expired callback signature")

    signed_payload = timestamp.encode("utf-8") + b"." + request_body
    expected = hmac.new(
        settings.IMAGE_CALLBACK_SECRET.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    received = signature.removeprefix("sha256=")

    if not hmac.compare_digest(expected, received):
        raise HTTPException(status_code=401, detail="Invalid callback signature")
```

The endpoint verifies the callback before updating the database:

```python
# C:\Ashmiwebportal\backend\app\api\v1\endpoints\admin_images.py

@router.post("/callback")
async def image_processing_callback(
    request: Request,
    data: ImageCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    _verify_image_callback_signature(
        request_body=body,
        timestamp=request.headers.get("X-Ashmi-Timestamp"),
        signature=request.headers.get("X-Ashmi-Signature"),
    )

    service = ImageService(db)
    if data.status == "completed":
        image = await service.process_callback(
            data.image_id,
            data.processed_url,
            data.medium_url,
            data.thumbnail_url,
        )
    else:
        image = await service.mark_processing_failed(data.image_id)
```

Tests added:

```text
C:\Ashmiwebportal\backend\app\tests\test_image_callback_auth.py
```

Test coverage:

- valid signature is accepted
- missing signature is rejected
- wrong signature is rejected
- expired timestamp is rejected
- missing secret returns server error

Result:

```text
5 passed
```

### How This Helps Without VPC

The backend no longer trusts the network location.

It trusts cryptographic proof.

Even though the callback endpoint is reachable through public AWS infrastructure, only the image processor Lambda with the shared secret can create a valid signature within the allowed time window.

## 3. AWS Throttling And WAF Are Outside App Code

### What Was The Risk?

Some security controls do not appear inside Python source code because they live in AWS configuration.

That creates a documentation and verification risk:

- a developer may inspect FastAPI code and assume rate limiting is missing
- another environment may be deployed without the same controls
- WAF may be attached but accidentally left in Count mode instead of Block mode

### What We Did

We verified the deployed AWS state:

```text
API Gateway throttling: verified
CloudFront WAF attached: verified
CloudFront WAF rate-based Block mode: verified
```

The important production lesson:

**External controls must be verified, not assumed.**

In this architecture, rate limiting is not an in-app feature. It is an AWS edge/API feature.

### How This Helps Without VPC

VPC controls where traffic can travel inside a private network.

But this e-commerce API must accept public customer traffic, so traffic shaping belongs before Lambda:

- CloudFront WAF handles abusive edge traffic
- API Gateway throttling handles API request rate and bursts
- Lambda focuses on valid business logic

## 4. Secrets Stored In Lambda Environment Variables

### What Was The Risk?

In development, we continue to use Lambda environment variables for simplicity.

AWS encrypts Lambda environment variables at rest, but they are still part of Lambda configuration. If too many people or automation roles can read Lambda configuration, sensitive values can be exposed.

Examples of sensitive configuration:

- `DATABASE_URL`
- `SECRET_KEY`
- `IMAGE_CALLBACK_SECRET`
- `PII_ENCRYPTION_KEY`
- `RAZORPAY_KEY_SECRET`
- `SMTP_PASSWORD`

### Current Decision

For development:

```text
Continue Lambda environment variables with restricted access.
```

For production:

```text
Use AWS Secrets Manager for high-value secrets.
Use AWS Systems Manager Parameter Store for non-secret or low-sensitivity runtime configuration.
```

SSM stands for **AWS Systems Manager**.

### How This Helps Without VPC

VPC does not solve secret management.

Secret exposure is mainly an IAM and configuration-management problem. Moving production secrets into dedicated AWS secret stores improves rotation, access control, and auditability without requiring VPC networking.

## 5. App-Level Security Headers

### What Was The Risk?

Security headers tell browsers how to safely handle responses.

Without them, the application can be more exposed to:

- clickjacking
- MIME sniffing
- referrer data leakage
- unsafe browser capabilities
- unsafe script or frame loading
- insecure HTTP downgrade in HTTPS environments

CloudFront can also apply response header policies, but we added FastAPI security headers so API responses have an application-level baseline.

![Security headers map](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/08-security-headers-map.png)

### What We Implemented

Middleware implementation:

```python
# C:\Ashmiwebportal\backend\app\middleware\security_headers.py

class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, enable_hsts: bool = False):
        self.app = app
        self.enable_hsts = enable_hsts

    async def __call__(self, scope, receive, send):
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
```

Configuration:

```python
# C:\Ashmiwebportal\backend\app\core\config.py

TRUSTED_HOSTS: list[str] = [
    "localhost",
    "127.0.0.1",
    "*.execute-api.ap-south-1.amazonaws.com",
]
ENABLE_SECURITY_HEADERS: bool = True
ENABLE_HSTS: bool = False
```

Middleware wiring:

```python
# C:\Ashmiwebportal\backend\app\main.py

if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=settings.ENABLE_HSTS,
    )

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS,
)
```

Tests added:

```text
C:\Ashmiwebportal\backend\app\tests\test_security_headers.py
```

Result:

```text
2 passed
```

### How This Helps Without VPC

VPC does not protect the browser.

Security headers are browser-facing controls. They reduce client-side risk even when the backend is intentionally public.

## Final Security Model

![Layered controls architecture](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/03-layered-controls.png)

Our final no-VPC security model is layered:

| Layer | Control |
|---|---|
| Edge | CloudFront CDN, WAF, TLS, DDoS resiliency |
| API | API Gateway throttling |
| Application | Authentication, HMAC callback verification, security headers, TrustedHost |
| Payments | Razorpay and Stripe signature verification |
| Data | SSL database connectivity and PII encryption |
| Secrets | Dev Lambda env vars, production Secrets Manager + SSM plan |

## Before And After

![Before and after controls](C:/Ashmiwebportal/generated/linkedin-no-vpc-security-article/05-before-after.png)

Before:

- public API without fully documented edge controls
- image callback accepted without cryptographic proof
- security headers were not clearly enforced from app code
- secrets were environment-variable based

After:

- CloudFront CDN is the front door
- CloudFront WAF rate-based rule is in Block mode
- API Gateway throttling is verified
- image callback uses HMAC signature verification
- FastAPI adds app-level security headers
- TrustedHost middleware is configured
- test coverage verifies callback authentication and headers
- production secret-store plan is defined

## The Main Takeaway

VPC is useful when the workload needs private network isolation.

But VPC is not a magic security switch.

For a public serverless e-commerce application, the better question is:

**Are the right protections placed before Lambda, inside the application, and around sensitive data?**

In this implementation, we overcame the absence of VPC by combining:

- CloudFront CDN and edge protection
- CloudFront WAF rate-based blocking
- API Gateway throttling
- HMAC-signed service callback
- App-level browser security headers
- TrustedHost validation
- payment webhook signature verification
- encrypted sensitive data
- production-ready secret management direction

That gives the platform a cost-conscious and understandable security model without forcing VPC/NAT cost into the architecture before it is truly needed.

## References

- [AWS NAT Gateway pricing](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-pricing.html)
- [AWS Shield documentation](https://docs.aws.amazon.com/shield/)
- [AWS Shield mitigation logic for CloudFront and Route 53](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation-logic-continuous-inspection.html)
- [AWS CloudFront response headers policies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/modifying-response-headers.html)
- [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [AWS Lambda environment variable encryption](https://docs.aws.amazon.com/lambda/latest/dg/security-encryption-at-rest.html)

---

Footer: This article is based on a real FastAPI + AWS Lambda e-commerce implementation reviewed in development. Production rollout should still include IAM review, secret rotation, monitoring, load testing, rollback drills, and environment-specific verification.
