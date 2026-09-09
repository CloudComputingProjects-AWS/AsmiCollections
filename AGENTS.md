# AGENTS.md

## Project Identity

- Project: `Ashmiwebportal`
- Workspace: `C:\Ashmiwebportal`
- Primary application shape:
  - FastAPI backend under `backend/`
  - Vite/React frontend under `frontend/`
  - AWS dev deployment via GitHub Actions, ECR, Lambda, S3, and CloudFront
- This file is intended to bootstrap context for new chat sessions in this repo.

## Current Branch / Deployment Model

- Active AWS dev deployment workflow: [deploy-dev-v3.yml](C:/Ashmiwebportal/.github/workflows/deploy-dev-v3.yml)
- Current dev trigger:
  - push to `develop`
- Current dev GitHub Environment:
  - `aws_dev`
- Current API Gateway dev stage direction:
  - `API_GATEWAY_STAGE=dev`
  - the HTTP API `dev` stage must exist and have default route throttling configured
  - when using a named stage, Lambda/Mangum must strip the `/dev` base path before FastAPI routing
- Current prod model agreed in project discussion:
  - validate in `aws_dev`
  - later promote to prod with separate `aws_prod` resources and role
- Important: older docs or comments that say dev deploys from `main` are stale unless the workflow file has been changed again.

## Architecture Overview

### Local development

- Frontend local dev server:
  - from `frontend/`
  - `npm run dev`
- Frontend Vite proxy:
  - `/api` -> `http://localhost:8000`
- Backend local host-run mode:
  - from `backend/`
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Local Docker mode:
  - from repo root
  - `docker compose up postgres api`

### AWS dev runtime

- Backend runtime:
  - AWS Lambda container image
- Frontend runtime:
  - static site in S3 behind CloudFront
- Image processing runtime:
  - separate Lambda container image
- Database:
  - Neon PostgreSQL, remotely hosted outside AWS account
- Important Lambda container-image meaning:
  - Lambda container image is the packaging format for function code and dependencies
  - it is not an ECS/Fargate task, service, cluster, or task definition
  - Lambda functions remain event-driven and stateless from an application-state perspective
  - durable state must stay outside the Lambda runtime, currently in Neon PostgreSQL, S3, SSM, and payment/provider systems
- Current AWS container runtime mental model:
  - ECR stores deployable container images such as `ashmi-backend-sg-dev:dev` and `ashmi-image-processor-sg-dev:dev`
  - Lambda functions reference those ECR images as their code package
  - API Gateway invokes `ashmi-backend-dev-sg`
  - S3 upload events should invoke the Singapore image processor Lambda for the full SG dev stack
  - no ECS task definition is expected for this deployment model
- Current dev region direction:
  - target dev region is `ap-southeast-1` (Asia Pacific Singapore)
  - backend/API latency work has moved the dev backend/API path toward Singapore to align with the Neon database region
  - the dev target is now a full Singapore stack for consistency: frontend S3, assets S3, backend/API, image processor, SSM parameters, and CloudFront configuration should all point at the SG dev resources
  - Mumbai `ap-south-1` dev resources are legacy during migration and are expected to be deleted from AWS after Singapore validation and cutover are complete

### Customer-facing runtime flow

- Customer opens the frontend through the active Singapore dev CloudFront distribution.
  - SG CloudFront domain is still to be finalized and then recorded in `FRONTEND_URL`, `CORS_ORIGINS`, and `IMAGE_CDN_DOMAIN` as appropriate.
  - Legacy Mumbai dev frontend currently observed during migration: `https://di156w1uc1xwk.cloudfront.net`
- Frontend app files should be served from `ashmi-dev-frontend-sg` behind the SG dev CloudFront distribution.
- Public catalogue browsing should call backend catalogue APIs through:
  - `VITE_API_URL=https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/api/v1`
- API Gateway invokes `ashmi-backend-dev-sg`.
- `ashmi-backend-dev-sg` runs FastAPI from the Lambda container image and reads catalogue, product, image metadata, user, cart, order, and payment records from Neon PostgreSQL.
- Customer browsing flow:
  - home / categories / shop / search
  - product detail
  - select variant, size, and quantity
  - add to cart
- Cart behavior:
  - guest cart starts in browser localStorage
  - authenticated cart uses backend cart APIs and Neon DB
  - after login, guest cart is intended to merge into the authenticated server cart
  - customer header cart count is sourced from [frontend/src/stores/cartStore.js](C:/Ashmiwebportal/frontend/src/stores/cartStore.js) `itemCount`
  - [frontend/src/components/layout/CustomerHeader.jsx](C:/Ashmiwebportal/frontend/src/components/layout/CustomerHeader.jsx) should fetch the authenticated cart when `user` becomes available and render the cart badge when `itemCount > 0`
  - [frontend/src/stores/authStore.js](C:/Ashmiwebportal/frontend/src/stores/authStore.js) should refresh cart state after normal login and 2FA login, and clear cart state on logout
- Checkout behavior:
  - `/cart` is public
  - `/checkout`, `/orders`, `/profile`, and `/addresses` are protected customer routes
  - unauthenticated customers are redirected to login before checkout
- Order placement flow:
  - checkout validates cart, stock, address, coupon, shipping fee, and total
  - checkout stock reservation now uses an atomic database update against `product_variants.stock_quantity`, so `stock_quantity` represents currently available sellable stock after reservation
  - the atomic reservation pattern is `UPDATE product_variants SET stock_quantity = stock_quantity - qty WHERE id = variant_id AND stock_quantity >= qty RETURNING id`; this is intended to prevent oversell while still selling all available stock under concurrent checkout pressure
  - `inventory_reservations.status='held'` records which pending order owns already-deducted reserved stock; payment success confirms the reservation, while payment failure/cancellation/expiry should release the reservation and restore stock
  - do not reintroduce the prior checkout lock-timeout pattern that used `SELECT ... FOR UPDATE`, counted held reservations separately, and could reject valid buyers before all available stock was sold
  - backend creates `orders` and `order_items` records in Neon
  - initial payment status is `pending`
  - payment gateway confirmation, polling, or webhook updates payment/order status
  - successful payment should move payment status to `paid`, confirm the existing reservation, and move order status toward confirmed/fulfillment flow without deducting stock a second time
  - live Razorpay UPI payment validation on the SG `aws_dev` stack passed on 2026-08-25 IST using order `ORD-20260824-DB3C48` / order id `47330275-a3ac-488c-b446-ef55b03e94b8`
  - Razorpay payment `pay_TTkFKWASfbCqkb` for Razorpay order `order_TTkEQ47p8CAuAb` was captured, recorded in Neon `payment_events` as `payment.captured`, and processed with `processed=true`
  - same-order payment re-attempt against `/payments/upi/collect` returned `400` with `Cannot initiate payment for order in 'confirmed' status`; the order remained `payment_status=paid`, `order_status=confirmed`, and the original gateway ids were unchanged
  - current remaining payment hardening is optional/non-blocking for this module: automated webhook replay coverage, concurrent frontend-verify plus webhook race testing, and provider-to-DB reconciliation reporting
- Bulk Inventory Mutation admin module is complete on the SG `aws_dev` stack as of 2026-08-31 IST:
  - admin bulk stock mutation means changing `product_variants.stock_quantity` for multiple variants in one admin write operation; it is separate from checkout stock reservation
  - frontend admin inventory calls `POST /admin/inventory/bulk-update`; backend also exposes canonical `PUT /admin/inventory/bulk`
  - route ordering in [backend/app/api/v1/endpoints/admin_products.py](C:/Ashmiwebportal/backend/app/api/v1/endpoints/admin_products.py) must keep static `PUT /inventory/bulk` before dynamic `PUT /inventory/{variant_id}` so FastAPI does not parse `bulk` as a UUID variant id
  - live SG real integration drill passed with `6 passed in 124.73s`, covering alias POST success, canonical PUT success, negative stock `422`, malformed variant id `422`, missing variant `404`, and B6 rollback drill
  - B6 rollback drill passed: a bulk request with one valid variant followed by one missing variant returned `404`, and the valid variant's original stock remained unchanged after re-query
  - optional future production hardening remains non-blocking for this completed module: pre-validate whole batch before mutation, reject duplicate variant IDs, add batch size limits, add inventory audit trail, and consider optimistic conflict protection

### Planned WhatsApp AI order chatbot

- Current CXO build plan PDF:
  - [output/pdf/whatsapp-ai-order-chatbot-cxo-plan.pdf](C:/Ashmiwebportal/output/pdf/whatsapp-ai-order-chatbot-cxo-plan.pdf)
- This WhatsApp-first plan supersedes the earlier app-login chatbot plan.
- User implementation preference:
  - do not change or deploy chatbot application code automatically unless the user explicitly asks
  - provide phase-wise frontend/backend/database implementation guidance first so the user can understand and apply changes manually
- Current direction:
  - build a customer-facing constrained ReAct order enquiry agent on the company WhatsApp Business account number
  - no separate customer chatbot frontend is required for Phase 1; customers interact through WhatsApp
  - the existing web UI may be extended only for WhatsApp activation, consent, verification, opt-out, profile preferences, and optional admin/support review
  - support questions about a customer's own order status, delivery status, payment status, ordered items, invoice availability, cancellation eligibility, refund state, delivery timeline, and recent orders
  - build reusable backend chatbot infrastructure, but keep Ashmi-specific authorization and order facts behind a safe domain adapter
  - use the internal ReAct loop `Reason -> Act -> Observe -> Validate -> Final`, with actions restricted to approved backend tools
- Current Phase 0 status as of 2026-09-10 IST:
  - Company WhatsApp Business sender-number ownership is no longer blocked.
  - A new dedicated customer-facing phone number was registered and verified directly with Meta WhatsApp Cloud API under the `Oshmi Clothing Collection` display name. It is not registered in WhatsApp Messenger or the WhatsApp Business mobile app.
  - The Meta payment method for the applicable WhatsApp Business Account was added and marked as default.
  - Outbound Cloud API messaging was validated manually: after a customer/test number opened the 24-hour customer-service window, an ordinary `type: text` request sent through Postman returned `HTTP 200 OK`. The dashboard `hello_world` failure was specific to that public-test-number template and did not indicate a failure of the real sender.
  - Initial FastAPI webhook code now exists locally in `backend/app/api/v1/endpoints/whatsapp.py`:
    - `GET /api/v1/whatsapp/webhook` validates `hub.mode` and the user-created verification token, then returns Meta's `hub.challenge` as plain text
    - `POST /api/v1/whatsapp/webhook` verifies `X-Hub-Signature-256` against the Meta App Secret, parses JSON, logs only a non-sensitive event summary, and acknowledges the event
    - the router is registered in `backend/app/api/v1/router.py`, producing `/api/v1/whatsapp/webhook` under the existing API v1 prefix
  - `backend/app/core/config.py` now supports direct local values and SSM parameter-name resolution for `META_WHATSAPP_WEBHOOK_VERIFY_TOKEN` and `META_WHATSAPP_APP_SECRET`.
  - AWS Singapore dev secret configuration is complete:
    - two matching SSM Parameter Store `SecureString` entries exist for the webhook verification token and Meta App Secret
    - `ashmi-backend-dev-sg` has the two corresponding `_PARAM` environment variables containing only the SSM parameter names
    - Lambda execution role `ashmi-lambda-role` has restricted `ssm:GetParameter` access through inline policy `AshmiWhatsAppSsmReadDev`
  - The webhook code is not deployed yet. It is currently in the working tree on `feature/aws-dev-sync`; `backend/app/api/v1/endpoints/whatsapp.py` remains untracked until deliberately staged.
  - Next webhook checkpoint:
    - stage only `whatsapp.py`, `config.py`, and `router.py`, keeping unrelated working-tree changes out of the webhook commit
    - commit and push the feature branch, then merge it into `develop` to trigger `.github/workflows/deploy-dev-v3.yml`
    - confirm the GitHub Actions deployment succeeds and the Lambda returns `HTTP 200` with the exact supplied challenge for an authenticated public GET verification request
    - then enter the deployed SG callback URL and the same verification token in Meta, click `Verify and save`, and subscribe the WABA webhook to the `messages` field
  - Meta Business Verification remains unverified because the business domain email, website, and business registration/GSTN are still under process. The Meta app is unpublished, so production webhook delivery remains restricted until applicable publication requirements are completed.
  - Phase 0 business/compliance items still open:
    - company WhatsApp Business number ownership confirmation
    - support hours definition
    - human escalation SLA definition
    - approved customer data fields list
    - retention policy confirmation
    - WhatsApp-first scope sign-off
    - exact opt-in and opt-out wording approval
- WhatsApp activation and consent model:
  - Updated user decision (2026-09-05): Create Account requires Phone and asks "Is this your Whatsapp number?" with Yes selected by default. Yes reuses the account phone and country code and activates immediately; No opts out. There is no separate registration WhatsApp number input. Login popup remains available, with Skip leaving preferences unchanged.
  - Separate customer WhatsApp number verification is removed. Migration `d713ab924e60` converts pending consent to active and removes `whatsapp_verified`; apply it after `6edbbb0cc9d5`. Historical migrations remain intact.
  - `active` represents consent only, not proof of phone ownership. Future access to private order facts must still use authenticated Ashmi account authorization. Company Meta registration and webhook signature verification are separate requirements.
  - Phase 1 stores WhatsApp activation fields on the existing `users` table instead of adding a separate `whatsapp_contacts` table
  - this is acceptable for the current one-user-to-one-active-WhatsApp-number relationship and avoids unnecessary operational overhead
  - proposed `users` fields include `whatsapp_number`, `whatsapp_country_code`, `whatsapp_wa_id`, `whatsapp_opt_in`, `whatsapp_opt_in_at`, `whatsapp_opt_out_at`, `whatsapp_activation_status`, and `whatsapp_last_seen_at`
  - login, register, profile, and order-confirmation UI may collect WhatsApp number and consent; login/account creation must continue if the customer declines WhatsApp activation
  - the bot may answer order-specific facts only with authenticated Ashmi account authorization and `whatsapp_opt_in=true`; a consented number alone does not establish ownership
  - customers must be able to opt out, and opt-out should stop WhatsApp support messages
  - Local Phase 0 technical groundwork has started:
    - Alembic migration `6edbbb0cc9d5_add_whatsapp_activation_fields_to_users.py` adds WhatsApp activation fields to the local Docker PostgreSQL `users` table.
    - Local Docker DB migration required manually updating `alembic_version` from stale missing revision `a0e4039f97fc` to known revision `c9f1a2d4e7b8`, then running `alembic upgrade head`.
    - `LoginPage.jsx` now shows a WhatsApp activation modal to eligible customers after successful login.
    - The modal supports three separate choices:
      - `Activate`: saves opt-in and sets `whatsapp_activation_status='active'`
      - `Skip`: closes the modal and continues login without changing WhatsApp status
      - `Opted Out`: saves opt-out and should set `whatsapp_activation_status='opted_out'`
    - The login modal should not require users to manually remove country code from a prefilled phone number; normalize phone prefill so the country code dropdown and number input are not duplicated.
    - Customer consent activates immediately without a separate WhatsApp verification step. Outbound Cloud API text messaging has been validated manually; initial webhook verification and signed-event acknowledgement are implemented locally but still require deployment, Meta callback verification, and `messages` subscription. Automated event processing and chatbot replies remain unimplemented.
- Authentication model:
  - WhatsApp sender phone/`wa_id` alone is not enough for sensitive order facts until mapped to a verified Ashmi user
  - for unknown, unverified, opted-out, or ambiguous senders, the bot should provide only a safe authentication/activation path or human handoff
  - derive `user_id` only from Ashmi's verified mapping/session logic; ignore any `user_id`, phone number, order ownership claim, or identity instruction supplied by WhatsApp message text or model tool arguments
  - every order tool must enforce `Order.user_id == authenticated_user.id` even if the model asks for another customer's order
- Backend/schema direction:
  - use FastAPI endpoints under a new `/api/v1/whatsapp` or `/api/v1/ai-chat` route family for webhook, activation, verification, and chat handling
  - verify Meta webhook challenge/signature, deduplicate inbound messages by Meta message id, and block forged or replayed webhook payloads
  - store Meta/provider credentials server-side only, preferably in SSM SecureString/config; never expose keys to frontend code
  - use Pydantic models for webhook payloads, chat request/response payloads, tool arguments, tool outputs, provider replies, redacted order DTOs, validation results, and human-handoff payloads
  - use Pydantic for API/DTO validation around database data; keep Alembic migrations, SQLAlchemy models, and database constraints as the actual database schema enforcement layer
  - suggested supporting tables include `whatsapp_message_events` for webhook idempotency/replay protection, `ai_chat_sessions`, `ai_chat_messages`, and `ai_chat_handoffs`
- Reuse boundaries:
  - reusable pieces are the WhatsApp webhook pattern, LLM gateway, ReAct runner, retention framework, guardrail framework, logging, DTO validation, and handoff pattern
  - not zero-configuration for every database-backed app; each app must provide a safe domain adapter that enforces its own authorization rules and exposes only approved customer-facing fields
  - Ashmi's first domain adapter should wrap existing order service methods instead of giving the model direct database access
- LLM provider strategy:
  - use a provider-agnostic LLM gateway
  - the gateway should run a constrained ReAct turn, not a free-form autonomous database agent
  - development evaluation priority is NVIDIA NIM free prototype first, Hugging Face open-weight model second, and OpenAI only as fallback/benchmark
  - consider OpenAI for production only if quality, reliability, support, compliance, and total-cost checks justify the paid dependency
  - provider pricing, model availability, free credits, and retention controls are external facts and must be rechecked before production decisions
- ReAct agent direction:
  - ReAct is the reasoning/action pattern, not permission to access the database freely
  - the model may reason about which fact is needed, but the `Act` step may call only approved backend tools
  - the `Observe` step must receive only Pydantic-validated, redacted, user-scoped DTOs from backend services
  - the `Validate` step must compare the draft answer against observed tool facts and customer-facing policy before replying
  - phase 1 should cap ReAct at two Act/Observe tool rounds per customer message, then answer from observed facts or hand off to human review
  - do not expose raw chain-of-thought, hidden reasoning, system prompts, developer instructions, or internal validation details to customers; a short customer-safe rationale such as "I checked your order record" is acceptable
- Guardrail and hallucination rules:
  - the model may answer order facts only from backend tool results or approved customer-facing policy text
  - no direct SQL, generic database query tool, ORM session, admin endpoint, unrestricted API tool, schema-inspection tool, or company-info lookup tool may be exposed to the model
  - allow only narrow phase-1 tools such as `list_recent_orders`, `get_order_summary`, `get_delivery_status`, `get_order_timeline`, `get_invoice_status`, `get_cancellation_options`, and `get_refund_status`
  - tool arguments must be schema-validated, and backend tools must enforce customer ownership even if the model asks for another user's order
  - redact internal IDs where unnecessary, payment gateway raw payloads, internal admin notes, SSM names, Lambda names, secrets, cost/margin data, supplier details, fraud signals, phone, email, and full address before sending data to the model
  - output validation must block unsupported delivery, refund, payment, tracking, invoice, or order-status claims
  - if tracking data, delivery confirmation, or expected delivery date is absent, the bot should say it cannot confirm that detail from the order record instead of inventing a tracking number or delivery promise
- Company-information protection:
  - the chatbot is a customer order-support assistant, not an admin assistant
  - it must not reveal backend architecture, deployment details, database schema, credentials, source code, system prompts, provider keys, supplier/vendor details, business margins, company finances, company bank details, internal business policy, company location details not meant for customers, internal notes, fraud signals, or other customers' data
- Chat context retention:
  - preserve minimal chat context for the last 7 days only
  - store Ashmi chat context in Neon with `expires_at` and cleanup expired sessions/messages/tool payloads automatically
  - do not rely on provider-hosted conversation/thread storage for the 7-day business requirement
  - old chat context may help resolve references such as "that order" only within 7 days, but fresh order/payment/delivery facts must still be fetched from backend tools before answering
  - delete expired chat history without deleting order, invoice, payment, return, refund, or audit records
- Human-in-loop:
  - create a support/admin review record for authentication failure, provider failure, tool failure, ambiguous data, missing/uncertain ETA, repeated output-validator block, refund/cancellation dispute, or explicit customer request for human help
  - show a safe customer message instead of letting the model guess in exception cases
- Security parameters to check during build:
  - `AI_CHAT_ENABLED` or `WHATSAPP_AI_CHAT_ENABLED` feature flag defaults off outside approved dev/test
  - CORS/trusted-origin and CSRF behavior must match the existing backend security pattern for credentialed writes
  - per-user, per-phone, and per-IP rate limits, daily message caps, provider timeout, max input messages, max output tokens, and fallback-attempt limits must be configured before enabling live usage
  - ReAct loop execution must enforce the max tool-round limit and block unapproved tool names or invalid tool arguments
  - provider keys must be stored server-side only, preferably in SSM SecureString parameters such as `META_WHATSAPP_TOKEN_PARAM`, `META_WHATSAPP_APP_SECRET_PARAM`, `NVIDIA_NIM_API_KEY_PARAM`, `HF_TOKEN_PARAM`, and `OPENAI_API_KEY_PARAM`
  - logs should include request id, user id hash, WhatsApp id hash, session id, provider, model, selected intent, tool name, validation result, failure reason, latency, and token counts, but not raw chain-of-thought, secrets, full WhatsApp number, full payment payloads, or unnecessary PII
  - test prompt injection, external data injection through WhatsApp text, sensitive information disclosure, excessive agency, system-prompt leakage, misinformation/hallucination, webhook replay, authentication bypass, and unbounded consumption scenarios before SG dev sign-off

### Payment idempotency workflow

Use idempotency to ensure that one intended payment operation creates one business outcome, even when an app, network, or gateway retries a request.

- Treat these as distinct cases:
  - duplicate client payment initiation: the same customer request is sent again because of a double-click or retry
  - duplicate webhook delivery: the gateway sends the same provider event again because it did not receive a timely `HTTP 200 OK`
  - genuine second payment: the gateway has a different payment/event ID because the customer actually paid again
- Client payment initiation should use a stable idempotency key scoped to the customer, order, and payment operation. Reuse that key only for a retry of the same attempt.
- Build a request fingerprint from immutable request details such as order ID, amount, currency, and payment operation. A reused key with a different fingerprint is a conflict, not a valid duplicate.
- Claim a new key atomically in durable storage, including the request fingerprint and an initial `processing` state. Use a database uniqueness guarantee and handle the unique-conflict path; a read-before-insert check alone is not sufficient under concurrent requests.
- For an existing client key:
  - matching fingerprint and `completed` state: return the stored result; do not create another gateway payment
  - matching fingerprint and `processing` state: return an in-progress result or wait for the stored result; do not start the operation again
  - matching fingerprint and terminal failure: return the stored failure and apply the defined retry policy
  - mismatched fingerprint: reject or alert; never reuse one idempotency key for a different payment request
- A new client key must still pass the order-level guard. Do not start another payment if the order is already paid or confirmed.
- Webhook processing is a separate idempotency boundary:
  - verify the provider signature before any lookup or business action
  - use the provider event/payment ID as `payment_events.gateway_event_id`
  - record and compare the webhook payload fingerprint (`payload_hash`) before classifying an existing event as a safe replay
  - atomically claim the new event, track `processing` and `completed` state, and execute payment/order/stock/history changes in one transaction boundary
  - for a matching, already-completed event, perform no business action and return `HTTP 200 OK` from the backend to the payment gateway
- A genuine second gateway payment has a different provider event ID, so event-level idempotency alone cannot stop it. The order-level paid/confirmed guard must prevent repeated order confirmation, stock deduction, invoice generation, and notification; retain the extra payment for reconciliation or refund.
- `payment_events` currently stores `gateway_event_id`, `payload_hash`, `processed`, and `processed_at`. It is retained with financial records; there is no explicit TTL/expiry column today. Define a finance/audit retention period and expire records only after that policy period and reconciliation checks.

### Product image storage model

- Image bytes are not stored in Neon.
- Neon stores image metadata and URL/reference fields such as:
  - `original_url`
  - `processed_url`
  - `medium_url`
  - `thumbnail_url`
  - `processing_status`
- Raw product image upload flow:
  - backend creates a pending image DB record
  - backend returns a pre-signed S3 upload URL
  - browser uploads the original image directly to S3 under `uploads/raw/{product_id}/{image_id}.{ext}`
  - for the full SG dev stack, DB `original_url` should store an S3 reference such as `s3://ashmi-dev-assets-sg/uploads/raw/...`
- Processed product image flow:
  - S3 raw upload event triggers the Singapore image processor Lambda, target name `ashmi-image-processor-dev-sg` if that is the final created function name
  - image processor reads the raw S3 object
  - image processor writes generated WebP variants back to S3 under `uploads/processed/{product_id}/...`
  - image processor calls the backend callback URL
  - backend verifies the HMAC callback signature and updates Neon with processed image URLs
- Public processed image URLs should use the configured SG CDN domain, for example:
  - `https://<sg-dev-cloudfront-domain>/uploads/processed/{product_id}/{image_id}.webp`
- If S3 only contains `uploads/raw/...` after an upload, the image pipeline is not completing and likely needs S3 trigger, Lambda logs, S3 `PutObject` permission, or callback verification troubleshooting.
- Admin image upload validation on the SG `aws_dev` stack passed on 2026-08-30 IST:
  - presigned upload to S3 passed after configuring bucket CORS on `ashmi-dev-assets-sg` for direct browser `PUT` from `https://db5l55bfhn85l.cloudfront.net`
  - narrow S3 CORS direction for current frontend upload code is to allow `PUT` from the SG frontend CloudFront origin with `AllowedHeaders` including `Content-Type`; avoid broad `AllowedHeaders: ["*"]` unless the upload code begins sending additional required headers
  - image processor completion passed for uploaded PNG, JPG, and WebP images; processed product images are served as generated WebP variants
  - multiple image upload passed with 6 uploaded images
  - delete image, set primary image, admin edit-page image display, and customer product-page image display passed
  - invalid file type validation passed by rejecting a GIF before upload with an unsupported-format message and without increasing image count
- Important 2026-08-30 SG image-serving lesson:
  - if a processed image request returns `200 OK` but `Content-Type: text/html`, CloudFront is serving the frontend app fallback HTML instead of the image object
  - root cause observed: `db5l55bfhn85l.cloudfront.net` did not yet have `ashmi-dev-assets-sg` as an origin and did not have a `/uploads/*` behavior
  - fix applied: add `ashmi-dev-assets-sg` as a CloudFront origin on distribution `E3TY6IMS9QZRVN`, create behavior `/uploads/*` above `Default (*)`, route it to the assets bucket origin, use Origin Access Control, update `ashmi-dev-assets-sg` bucket policy to allow CloudFront service principal with `AWS:SourceArn=arn:aws:cloudfront::762813627344:distribution/E3TY6IMS9QZRVN`, and invalidate `/uploads/*`
  - expected healthy processed image response is `Status Code: 200 OK` with `Content-Type: image/webp`
- CDN render validation for admin product images passed on 2026-08-31 IST:
  - after adding frontend tab persistence in [frontend/src/pages/admin/ProductForm.jsx](C:/Ashmiwebportal/frontend/src/pages/admin/ProductForm.jsx), refreshing the product edit page with the Images tab selected kept focus on `Images`
  - processed image requests under `https://db5l55bfhn85l.cloudfront.net/uploads/processed/...` returned `200 OK`
  - response headers showed `Content-Type: image/webp`, `Cache-Control: public, max-age=31536000, immutable`, and a non-empty image content length
  - Chrome DevTools Preview rendered the actual processed product image, confirming CloudFront served image bytes rather than frontend HTML

## Local Runtime Rules

Use exactly one local backend mode at a time.

### Mode A: backend runs directly on Windows

- File that matters: [backend/.env](C:/Ashmiwebportal/backend/.env)
- Database host must be:
  - `localhost:5432`
- Reason:
  - the backend process is running on the host machine

### Mode B: backend runs inside Docker Compose

- File that matters: [docker-compose.yml](C:/Ashmiwebportal/docker-compose.yml)
- Database host must be:
  - `postgres:5432`
- Reason:
  - `api` container reaches the `postgres` service through Docker service DNS

### Frontend local rule

- Frontend never talks to Postgres directly
- Frontend only talks to backend API through the Vite proxy

### Important warning

- Do not mix:
  - host-run backend using `backend/.env`
  - Docker API container using `docker-compose.yml`
- Mixing modes is a frequent cause of:
  - `socket hang up`
  - startup DB connection failures
  - login confusion that is not actually caused by password issues

## Local Commands

### Frontend

- `cd C:\Ashmiwebportal\frontend`
- `npm run dev`
- `npm run build`
- `npm run lint`
- `npm run preview`

### Backend host-run

- `cd C:\Ashmiwebportal\backend`
- `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### Docker local stack

- `cd C:\Ashmiwebportal`
- `docker compose up postgres api`

### Playwright

- E2E specs:
  - `frontend/src/tests/e2e/`
- Config:
  - `frontend/playwright.config.js`
- Typical run:
  - `npx playwright test`

## AWS Dev Resources

Singapore is the target dev baseline for future work. Mumbai resources are retained in this document only as legacy migration references until they are deleted from AWS after the Singapore cutover is validated.

### IAM / OIDC

- GitHub OIDC provider exists in the single AWS account
- Dev deploy role:
  - `GitHubActions-Ashmiwebportal-Deploy-Dev`
- Prod deploy role:
  - `GitHubActions-Ashmiwebportal-Deploy-Prod`

### Singapore dev compute and storage target

These resources define the full `ap-southeast-1` dev stack direction. Use them as the current dev target unless AWS has been intentionally changed later.

- Singapore backend ECR repository:
  - `ashmi-backend-sg-dev`
- Singapore image processor ECR repository:
  - `ashmi-image-processor-sg-dev`
- Singapore backend Lambda:
  - `ashmi-backend-dev-sg`
- Singapore backend Lambda execution role:
  - currently reuses `ashmi-lambda-role`
- Singapore backend Lambda runtime shape:
  - package type: Lambda container image
  - architecture: `x86_64`
  - memory: `512 MB`
  - timeout: `30 seconds`
  - AWS account Lambda concurrent execution quota in `ap-southeast-1`: `1000`
  - reserved concurrency for `ashmi-backend-dev-sg`: `400`
- Singapore backend HTTP API:
  - name: `ashmi-backend-dev-sg-api`
  - API ID: `r5k4xtwcpi`
  - stage: `dev`
  - route: `$default`
  - invoke URL: `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev`
- Singapore backend health check:
  - `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/health`
  - verified on 2026-07-18 as:
    - `200`
    - `{"status":"healthy","version":"2.5.0","environment":"aws_dev"}`
  - re-verified on 2026-08-17 IST as:
    - public API Gateway `/dev/health`: `200`
    - direct Lambda invoke for `ashmi-backend-dev-sg`: app-level `200 healthy`
  - a transient public API Gateway `500` was observed immediately before the successful 2026-08-17 recheck, while direct Lambda health was healthy; if this recurs, inspect API Gateway/Lambda invocation path and logs before assuming app-code failure
  - after the 2026-08-17 GitHub/Lambda environment cleanup, browser check returned:
    - `200`
    - `{"status":"healthy","version":"2.5.0","environment":"aws_dev"}`
- Singapore frontend S3 bucket for full SG dev stack:
  - `ashmi-dev-frontend-sg`
- Singapore assets S3 bucket:
  - `ashmi-dev-assets-sg`
- Singapore CloudFront distribution:
  - current SG dev distribution ID observed in GitHub `aws_dev`:
    - `E3TY6IMS9QZRVN`
  - current SG dev frontend CloudFront domain:
    - `https://db5l55bfhn85l.cloudfront.net`
  - browser validation on 2026-08-17 showed the Ashmi frontend loading from this domain
  - `FRONTEND_URL`, `CORS_ORIGINS`, and `IMAGE_CDN_DOMAIN` should remain aligned to the active SG CloudFront domain as appropriate
- Singapore frontend API base secret:
  - `VITE_API_URL=https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/api/v1`
- Singapore SSM dev parameter names:
  - `/ashmi/dev/database-url-sg`
  - `/ashmi/dev/database-url-sync-sg`
  - `/ashmi/dev/image-callback-secret-sg`
- Singapore backend assets bucket name selected for Lambda env:
  - `ashmi-dev-assets-sg`

### Legacy Mumbai dev resources

These are legacy migration references only. Do not use them for new dev work after SG cutover. The user intends to delete Mumbai-related AWS resources after the Singapore migration is validated.

- Legacy backend ECR repository:
  - `ashmi-backend`
- Legacy image processor ECR repository:
  - `ashmi-image-processor`
- Legacy backend Lambda:
  - `ashmi-backend-dev`
- Legacy image processor Lambda:
  - `ashmi-image-processor-dev`
- Legacy frontend S3 bucket:
  - `ashmi-dev-frontend`
- Legacy assets S3 bucket:
  - `ashmi-dev-assets`
- Legacy CloudFront distribution ID:
  - `E32QTT8QPXCW64`
- Legacy frontend domain observed in project work:
  - `di156w1uc1xwk.cloudfront.net`
- Legacy HTTP API ID:
  - `9amq4q9qa4`
- Legacy API Gateway URL:
  - `https://9amq4q9qa4.execute-api.ap-south-1.amazonaws.com/dev`
- Legacy frontend API base:
  - `VITE_API_URL=https://9amq4q9qa4.execute-api.ap-south-1.amazonaws.com/dev/api/v1`

Important Singapore API Gateway / Lambda lessons:

- Lambda container images pushed from Docker Desktop/buildx must be Lambda-compatible single-image manifests.
  - If ECR shows `dev` as an Image Index and Lambda creation fails with unsupported manifest/config/layer media type, rebuild/push with:
    - `docker buildx build --platform linux/amd64 --provenance=false --sbom=false ... --push`
- Because the backend image is built for `linux/amd64`, the Lambda must be `x86_64`, not `arm64`.
- The Lambda add-trigger flow can create an unwanted route such as `ANY /ashmi-backend-dev-sg`.
  - The backend API should use `$default` so FastAPI receives `/health` and `/api/v1/...` paths.
- API Gateway invoke permission for `$default` may need this Lambda resource-policy Source ARN:
  - `arn:aws:execute-api:ap-southeast-1:762813627344:r5k4xtwcpi/*/$default`
- A broader route permission was also added during troubleshooting:
  - `arn:aws:execute-api:ap-southeast-1:762813627344:r5k4xtwcpi/*/*/*`
- If API Gateway returns `500` and no fresh Lambda log stream/events appear, check Lambda resource policy and route/integration permissions before debugging app code.
- For Singapore backend and image processor env, `DATABASE_URL_PARAM`, `DATABASE_URL_SYNC_PARAM`, and `IMAGE_CALLBACK_SECRET_PARAM` must point to the selected SG SSM names above.
- `CORS_ORIGINS` should be JSON-list shaped and must include the active SG CloudFront frontend origin, for example:
  - `["https://<sg-dev-cloudfront-domain>"]`
- `FRONTEND_URL` should also be the active SG CloudFront frontend origin so password-reset links point to the SG stack.
- `TRUSTED_HOSTS` should be JSON-list shaped and contain hostnames only, not URL origins. For the current SG dev stack:
  - `["localhost","127.0.0.1","*.execute-api.ap-southeast-1.amazonaws.com","db5l55bfhn85l.cloudfront.net"]`
  - do not use `https://db5l55bfhn85l.cloudfront.net` inside `TRUSTED_HOSTS`; that causes `Invalid host header`
  - do not leave only the legacy Mumbai API wildcard `*.execute-api.ap-south-1.amazonaws.com` in SG `TRUSTED_HOSTS`; the Singapore API Gateway host is under `*.execute-api.ap-southeast-1.amazonaws.com`
- Do not set `AWS_REGION` manually in Lambda environment variables.

## GitHub Environment Contract

### `aws_dev` variables currently expected by workflow

- `APP_NAME`
- `APP_VERSION`
- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME`
- `API_GATEWAY_ID`
- `API_GATEWAY_STAGE`
- `CORS_ORIGINS`
- `CLOUDFRONT_DISTRIBUTION_ID`
- `ECR_REPOSITORY`
- `ENABLE_HSTS`
- `ENABLE_SECURITY_HEADERS`
- `ENVIRONMENT`
- `FRONTEND_URL`
- `IMAGE_CALLBACK_SECRET_PARAM`
- `IMAGE_CDN_DOMAIN`
- `IMAGE_PROCESSOR_ECR_REPOSITORY`
- `IMAGE_PROCESSOR_LAMBDA_FUNCTION_NAME`
- `JWT_ALGORITHM`
- `LAMBDA_FUNCTION_NAME`
- `EXPECTED_API_THROTTLE_BURST`
- `EXPECTED_API_THROTTLE_RATE`
- `DATABASE_URL_PARAM`
- `DATABASE_URL_SYNC_PARAM`
- `S3_FRONTEND_BUCKET`
- `TRUSTED_HOSTS`

### `aws_dev` secrets currently expected by workflow

- `VITE_API_URL`

Important image callback secret rule:

- `IMAGE_CALLBACK_SECRET` has been removed from GitHub `aws_dev` secrets.
- Do not re-add `IMAGE_CALLBACK_SECRET` as a GitHub secret for the Singapore dev path.
- Both backend and image processor Lambdas should use the `IMAGE_CALLBACK_SECRET_PARAM` environment variable, whose value is the SSM SecureString parameter name.

### Backend Lambda runtime settings synced by workflow

As of the current verified workflow direction, [deploy-dev-v3.yml](C:/Ashmiwebportal/.github/workflows/deploy-dev-v3.yml) syncs these backend Lambda runtime settings automatically:

- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT`
- `API_GATEWAY_ID`
- `API_GATEWAY_STAGE`
- `EXPECTED_API_THROTTLE_BURST`
- `EXPECTED_API_THROTTLE_RATE`
- `FRONTEND_URL`
- `JWT_ALGORITHM`
- `IMAGE_CALLBACK_SECRET_PARAM`
- `DATABASE_URL_PARAM`
- `DATABASE_URL_SYNC_PARAM`
- `CORS_ORIGINS`
- `TRUSTED_HOSTS`
- `ENABLE_SECURITY_HEADERS`
- `ENABLE_HSTS`

Therefore, backend SSM parameter names, AWS protection expectation values, and other non-secret runtime settings should be maintained in GitHub `aws_dev` and should target `ashmi-backend-dev-sg` for the full Singapore dev stack after workflow cutover.

Important Lambda environment rule:

- GitHub `aws_dev` variables are deployment-time source of truth; Lambda environment variables are the runtime copy used by `ashmi-backend-dev-sg`.
- After changing GitHub `aws_dev` variables such as `DATABASE_URL_PARAM`, `DATABASE_URL_SYNC_PARAM`, `IMAGE_CALLBACK_SECRET_PARAM`, `TRUSTED_HOSTS`, `FRONTEND_URL`, or `CORS_ORIGINS`, rerun `deploy-dev-v3.yml` so the workflow syncs them into the backend Lambda runtime environment.
- If the live API still shows old SSM parameter names or old host validation behavior after GitHub values are corrected, inspect the live Lambda environment variables before debugging code.
- Keep `AWS_REGION=ap-southeast-1` as a GitHub `aws_dev` variable for the SG dev stack because AWS CLI commands need `--region`.
- Do not include `AWS_REGION` inside the Lambda `Environment.Variables` update payload.
- Lambda provides `AWS_REGION` automatically at runtime and rejects attempts to set it manually because it is a reserved key.
- Lambda environment variable values must be strings. In workflow `jq` payload construction, use `--arg`, not `--argjson`, for values such as `EXPECTED_API_THROTTLE_BURST` and `EXPECTED_API_THROTTLE_RATE`.

## Backend Runtime Configuration Truths

### Config file intent

- [backend/app/core/config.py](C:/Ashmiwebportal/backend/app/core/config.py) is intentionally being used as a schema/defaults definition layer
- Sensitive runtime values should come from environment variables, not hard-coded secrets in the file
- The user previously chose to keep some values blank in code and source them from environment/runtime configuration
- Current intended pattern:
  - local development may provide direct values such as `DATABASE_URL`, `DATABASE_URL_SYNC`, and `IMAGE_CALLBACK_SECRET` in `backend/.env`
  - AWS Lambda should provide `DATABASE_URL_PARAM`, `DATABASE_URL_SYNC_PARAM`, and `IMAGE_CALLBACK_SECRET_PARAM`
  - backend code must resolve `_PARAM` names from AWS SSM Parameter Store before use
  - image processor Lambda code should use `IMAGE_CALLBACK_SECRET_PARAM`; any old raw `IMAGE_CALLBACK_SECRET` Lambda environment variable is stale cleanup only and should not be used by code
- Verified 2026-08-17 troubleshooting lesson:
  - an SSM `AccessDeniedException` for `/ashmi/dev/database-url` was not JWT-related
  - it meant the live Lambda runtime was still trying to read the old non-SG parameter name
  - the fix was to align GitHub `aws_dev` variables and the live `ashmi-backend-dev-sg` Lambda environment with the SG parameter names, and ensure `ashmi-lambda-role` had `ssm:GetParameter`/`ssm:GetParameters` for those SG parameter ARNs

### Database URLs

- Local host-run backend:
  - use `localhost`
- Local Docker backend:
  - use `postgres`
- AWS Lambda backend:
  - use a real hosted database endpoint
  - currently Neon PostgreSQL
  - not `localhost`
  - not `postgres`
- For current SSM-backed `aws_dev` direction:
  - `DATABASE_URL_PARAM` should point to the async DB URL parameter name
  - `DATABASE_URL_SYNC_PARAM` should point to the sync migration DB URL parameter name
  - the parameter values themselves must contain the actual Neon connection strings

### Neon connection guidance

- Current backend DB code uses `asyncpg` with `NullPool` for `aws_dev` / `production`
- For the current code path, use the direct Neon host for backend runtime URLs, not the `-pooler` host
- `DATABASE_URL` should use the async SQLAlchemy driver format:
  - `postgresql+asyncpg://USER:PASSWORD@DIRECT_NEON_HOST/DB_NAME`
- `DATABASE_URL_SYNC` should use the sync migration driver format:
  - `postgresql+psycopg2://USER:PASSWORD@DIRECT_NEON_HOST/DB_NAME?sslmode=require`
- If using SSM in `aws_dev`:
  - the SecureString value stored at `DATABASE_URL_PARAM` must be the full async URL above
  - the SecureString value stored at `DATABASE_URL_SYNC_PARAM` must be the full sync URL above
- For `asyncpg`, do not include `?sslmode=require` in the async SSM URL; the backend code supplies async SSL through driver connect args.
- Prior 2026-08-19 AWS dev failures were caused by malformed SSM database URL values:
  - a newline in `/ashmi/dev/database-url-sg` made the database name resolve incorrectly
  - `?sslmode=require` in the asyncpg URL caused `TypeError: connect() got an unexpected keyword argument 'sslmode'`
- If Neon shows a pooled host like `ep-xxx-pooler...`, remove `-pooler` or turn connection pooling off in the Neon connection modal to get the direct host
- Cross-region latency was the reason for the SG migration; after full SG cutover, compare endpoint timings before adding more app-level optimization

## Current Deployment Workflow Behavior

The current dev workflow has three jobs:

1. `deploy-image-processor`
2. `deploy-backend`
3. `deploy-frontend`

Important details:

- `deploy-backend` depends on `deploy-image-processor`
- image processor config is synced before image deployment
- backend deploy now performs deployment-time AWS protection validation before rollout
- backend Lambda config is synced before backend image deployment
- backend and image processor secret handling now use SSM parameter names for image callback secret consistency:
  - backend Lambda receives `IMAGE_CALLBACK_SECRET_PARAM` and resolves the SecureString from SSM
  - image processor Lambda receives `IMAGE_CALLBACK_SECRET_PARAM`, resolves the same SecureString from SSM, and uses it to sign callbacks
  - GitHub `aws_dev` no longer needs the raw `IMAGE_CALLBACK_SECRET` secret for this path
  - removing `IMAGE_CALLBACK_SECRET` from an existing Lambda environment is only hygiene for stale deployments; it is not required for `IMAGE_CALLBACK_SECRET_PARAM` to work
- frontend build uses `VITE_API_URL`
- `VITE_API_URL` is also used to derive image processor callback URL:
  - `${VITE_API_URL%/}/admin/images/callback`
- frontend artifacts are uploaded to S3 and then CloudFront is invalidated
- backend rollout should fail if API Gateway throttling or CloudFront WAF rate-based protections are absent or weaker than expected

### Dev stage / API Gateway path handling

- `aws_dev` is moving to named HTTP API stage `dev`, not `$default`.
- For named stage `dev`, direct API Gateway URLs include `/dev` before the application path.
- Backend FastAPI routes still start at `/health` and `/api/v1/...`, not `/dev/health`.
- [backend/lambda_handler.py](C:/Ashmiwebportal/backend/lambda_handler.py) must configure Mangum with `api_gateway_base_path` derived from `API_GATEWAY_STAGE` so `/dev` is stripped before FastAPI routing.
- If `API_GATEWAY_STAGE` is `$default` or blank, the Mangum base path should remain `/`.
- Browser/frontend calls for the SG dev stack should use:
  - `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/api/v1`
- A direct health check for the SG named stage should be:
  - `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/health`
- If `/dev/health` returns FastAPI `404`, the request is reaching Lambda but `/dev` is not being stripped before routing.

### WAF / CloudFront validation details

- CloudFront-associated WAFv2 Web ACLs are global scope and are managed through `us-east-1`, even when app resources are in `ap-southeast-1`.
- Current SG CloudFront distribution `E3TY6IMS9QZRVN` is associated with Web ACL:
  - `arn:aws:wafv2:us-east-1:762813627344:global/webacl/CreatedByCloudFront-32e3c457/393375cc-b355-4e50-a1fe-5b044f886b2e`
- On 2026-08-17, IAM simulation for `GitHubActions-Ashmiwebportal-Deploy-Dev` showed `wafv2:GetWebACL` is allowed for the SG Web ACL, so the remaining validation failure is not an IAM deny.
- On 2026-08-17, the SG Web ACL rules inspected from AWS contained only managed rule groups:
  - `AWSManagedRulesAmazonIpReputationList`
  - `AWSManagedRulesCommonRuleSet`
  - `AWSManagedRulesKnownBadInputsRuleSet`
- Earlier on 2026-08-17, the workflow failed closed with `CloudFront WAF has no top-level rate-based rules`; after subsequent AWS/GitHub variable cleanup, `deploy-dev-v3.yml` completed successfully.
- If this validation failure recurs, confirm the SG Web ACL has a top-level `RateBasedStatement` with `Action.Block`.
- In the AWS WAF console, use `AWS WAF -> Protection packs (web ACLs) -> CreatedByCloudFront-32e3c457 -> Rules`; do not use `AWS Shield -> Overview` for this Web ACL edit.
- Legacy Mumbai CloudFront Web ACL observed from distribution `E32QTT8QPXCW64`:
  - `arn:aws:wafv2:us-east-1:762813627344:global/webacl/CreatedByCloudFront-2e10ea00/9367cc21-b3c2-4187-83a3-2ac4dce74d8e`
- When parsing that ARN after `cut -d: -f6`, the slash fields are:
  - `global`
  - `webacl`
  - `CreatedByCloudFront-2e10ea00`
  - `9367cc21-b3c2-4187-83a3-2ac4dce74d8e`
- Therefore workflow shell parsing must use:
  - `WEB_ACL_NAME=$(echo "$WEB_ACL_ID" | cut -d: -f6 | cut -d/ -f3)`
  - `WEB_ACL_UUID=$(echo "$WEB_ACL_ID" | cut -d: -f6 | cut -d/ -f4)`
- Do not use `cut -d/ -f2` for the Web ACL name; that returns the literal resource type `webacl` and causes `WAFNonexistentItemException`.
- The same ARN parsing rule applies to [backend/app/utils/verify_aws_edge_protection.py](C:/Ashmiwebportal/backend/app/utils/verify_aws_edge_protection.py): resource parts index `2` is the Web ACL name and index `3` is the UUID.

### Frontend API base behavior

- [frontend/src/api/apiClient.js](C:/Ashmiwebportal/frontend/src/api/apiClient.js) uses `import.meta.env.VITE_API_URL || '/api/v1'` as its Axios base URL.
- For `aws_dev` named stage `dev`, `VITE_API_URL` must include `/dev/api/v1`.
- Auth refresh must use the configured Axios client, for example `apiClient.post('/auth/refresh', {})`, not raw `axios.post('/api/v1/auth/refresh', ...)`.
- A raw browser-relative `/api/v1/...` request from the deployed frontend goes to the CloudFront frontend domain, not directly to API Gateway, unless CloudFront is explicitly configured to route that path to the API origin.
- Current SG `aws_dev` frontend/API shape is cross-site:
  - frontend origin: `https://db5l55bfhn85l.cloudfront.net`
  - API origin: `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com`
  - because these are different sites, browser auth cookies from API Gateway are treated as third-party cookies by Chrome when requests are initiated from the CloudFront frontend.
- With this cross-site `aws_dev` shape and no CloudFront `/api/*` API origin behavior, `aws_dev` auth cookies must use `SameSite=None; Secure=True; HttpOnly=True`; `SameSite=Strict` causes login/2FA to return `200` but the immediate `/auth/me` call returns `401` because the cookie is not sent.
- Browser validation can still fail if Chrome blocks third-party cookies for the CloudFront site. If logs show `POST /api/v1/auth/login 200` or `POST /api/v1/auth/2fa/validate 200` followed immediately by `GET /api/v1/auth/me 401`, check DevTools `Cookies` for blocked `access_token` and allow third-party cookies for the dev frontend site.

## Branch / PR Review Language

- If no GitHub pull request has been opened yet, do not call a review an actual PR review
- For work on `feature/aws-dev-sync` before PR creation, describe review scope as:
  - pre-PR branch review of `feature/aws-dev-sync` against `develop`
- Use this local comparison for the prospective PR diff:
  - `git diff develop...HEAD`
- A real PR review should only be claimed after a GitHub PR exists and the PR metadata / files changed / CI status are available

## Security / Auth / Rate Limiting Truths

### OIDC

- GitHub Actions uses OIDC role assumption
- Long-lived AWS keys are not meant to be used for deploys

### Passwords

- User passwords are stored as bcrypt hashes
- Bcrypt hashes cannot be decrypted back to plain text
- Account recovery means password reset, not password retrieval
- Password reset emails use `FRONTEND_URL` from backend settings
- Local default is `http://localhost:3000`
- For the full SG dev stack, `aws_dev` should set `FRONTEND_URL` to the active SG CloudFront frontend domain, for example:
  - `https://<sg-dev-cloudfront-domain>`
- Reset links should therefore route to:
  - local: `http://localhost:3000/reset-password?token=...`
  - `aws_dev` SG stack: `https://<sg-dev-cloudfront-domain>/reset-password?token=...`

### 2FA

- Admin 2FA has worked in `aws_dev` during previous validation
- TOTP failures can still occur if:
  - the wrong authenticator secret is being used
  - the code expires
  - the device clock is off
### CSRF / Origin Policy

- Cookie SameSite policy must match frontend/API site topology:
  - same-site frontend/API topology: prefer `SameSite=Strict; Secure=True`
  - cross-site frontend/API topology, such as current SG `aws_dev` CloudFront frontend plus direct API Gateway API: use `SameSite=None; Secure=True; HttpOnly=True`
- Because `SameSite=None` allows cookies on cross-site browser requests, browser-driven state-changing routes must enforce strict `Origin` validation.
- Do not use one large global allowlist for every runtime path
- Use route-scoped policy instead:
  - browser-cookie routes such as `/api/v1/auth/`, `/api/v1/auth/2fa/`, and browser-driven admin write routes should require an allowed `Origin`
  - machine-to-machine routes such as image callbacks and payment webhooks should be exempt from `Origin` checks and instead rely on stronger service authentication such as HMAC signatures or webhook verification
- Preferred allowlist source for browser routes:
  - `FRONTEND_URL`
  - `CORS_ORIGINS`
- Preferred behavior:
  - enforce `Origin` only for `POST`, `PUT`, `PATCH`, and `DELETE`
  - reject missing or mismatched `Origin` with `403`
- Current verified codebase status:
  - shared Origin guard exists in [backend/app/core/origin_policy.py](C:/Ashmiwebportal/backend/app/core/origin_policy.py)
  - trusted browser origins are derived from:
    - `FRONTEND_URL`
    - `CORS_ORIGINS`
  - the guard is already applied across auth, 2FA, admin products, admin images, cart/coupons, orders, shipping/returns, reviews, payments, privacy, user profile, admin dashboard, admin settings, and invoice-regeneration write routes
  - machine-to-machine routes remain exempt from `Origin` checks and instead use signature-based verification:
    - image callback in [backend/app/api/v1/endpoints/admin_images.py](C:/Ashmiwebportal/backend/app/api/v1/endpoints/admin_images.py)
    - Razorpay webhook in [backend/app/api/v1/endpoints/payments.py](C:/Ashmiwebportal/backend/app/api/v1/endpoints/payments.py)
    - Stripe webhook in [backend/app/api/v1/endpoints/payments.py](C:/Ashmiwebportal/backend/app/api/v1/endpoints/payments.py)
  - previously noted `POST /api/v1/admin/refunds` Origin-policy gap is now protected in current code by `Depends(require_trusted_origin)` in [backend/app/api/v1/endpoints/shipping_returns.py](C:/Ashmiwebportal/backend/app/api/v1/endpoints/shipping_returns.py)
  - no automated Origin-policy test coverage was found under `backend/app/tests`

### Public catalogue stock visibility

- Customer-facing catalogue surfaces should not display products that have no purchasable inventory.
- Public product visibility rule:
  - product must be active
  - product must not be deleted
  - at least one active, non-deleted variant must have `stock_quantity > 0`
- Apply this rule in backend public catalogue queries, not only in frontend rendering:
  - product listing: [backend/app/services/catalog_service.py](C:/Ashmiwebportal/backend/app/services/catalog_service.py)
  - landing featured products
  - product detail by slug/id
  - search autocomplete
  - public filter options such as brands, sizes, and colors
- Admin product and inventory pages should still show zero-stock products so stock can be replenished or products can be managed.
- Product detail for a public slug whose active variants all have zero stock should return `404 Product not found` or an equivalent not-for-sale public response; do not allow Add to Cart for zero-stock variants.
- Public listing product cards in [frontend/src/components/catalog/ProductCard.jsx](C:/Ashmiwebportal/frontend/src/components/catalog/ProductCard.jsx) should show total purchasable inventory by summing `stock_quantity` across the public `product.variants` payload.
- When implementing this in SQLAlchemy, build a boolean condition such as `Product.id.in_(select(ProductVariant.product_id).where(...))`; do not pass a subquery object itself directly to `.where(...)`.

### Rate limiting architecture

Current project direction is AWS-side protection, not app-side Redis middleware.

- `RateLimitMiddleware` is intentionally not active
- Redis-based app rate limiter was removed from active architecture
- Current protection depends on:
  - API Gateway throttling
  - WAF rate-based rules
  - managed WAF protections
  - application validation/auth logic
- Current deployment direction:
  - GitHub Actions should validate API Gateway throttling and CloudFront WAF association before backend rollout
  - deploy should fail closed when those protections are absent or below expected thresholds

### Verified / required `aws_dev` protection baseline

- SG API ID:
  - `r5k4xtwcpi`
- Stage name:
  - `dev`
- Expected default API throttling baseline:
  - burst: `5000`
  - rate: `2500`
- API Gateway account throttling observed in `ap-southeast-1`:
  - burst: `5000`
  - rate: `10000`
- Lambda concurrency baseline for the SG dev load-test path:
  - account concurrent execution quota: `1000`
  - `ashmi-backend-dev-sg` reserved concurrency: `400`
- SG CloudFront distribution:
  - to be created/configured for the full SG dev stack and then stored in GitHub `aws_dev` as `CLOUDFRONT_DISTRIBUTION_ID`
- WAF protections required before treating SG dev as fully cut over:
  - rate-based block rule
  - AWS managed IP reputation
  - AWS managed common rules
  - AWS managed known bad inputs
- Source of truth for these values:
  - API Gateway stage configuration in AWS Console
  - CloudFront distribution WAF association in AWS Console
- Legacy Mumbai baseline for historical reference only:
  - API ID `9amq4q9qa4`
  - CloudFront distribution `E32QTT8QPXCW64`
  - Web ACL `CreatedByCloudFront-2e10ea00`

### Verified `aws_dev` load-test findings

- Load-test tool:
  - k6 installed on Windows at `C:\Program Files\k6\k6.exe`
  - test script: [tests/load/ashmi-2000-users.k6.js](C:/Ashmiwebportal/tests/load/ashmi-2000-users.k6.js)
- Current Neon plan used for AWS dev testing:
  - Neon Free plan
  - Free plan is suitable for smoke/cautious dev testing, not proof of 2,000 production users
- Verified clean public-catalog load-test results on 2026-08-19:
  - `50` VUs for `5m`: `http_req_failed_rate=0`, `429_count=0`, `5xx_count=0`, `p95_ms=259.035675`
  - `100` VUs for `5m`: `http_req_failed_rate=0`, `429_count=0`, `5xx_count=0`, `p95_ms=321.0658`
  - `250` VUs for `3m`: `http_req_failed_rate=0`, `429_count=0`, `5xx_count=0`, `p95_ms=373.83563`
  - `500` VU load-stage run after raising backend Lambda reserved concurrency to `400`: `http_reqs=131549`, `http_req_failed_rate=0`, `429_count=0`, `5xx_count=0`, `p95_ms=300.39404`
  - `500` VU confirmation run after raising backend Lambda reserved concurrency to `400`: `http_reqs=131584`, `http_req_failed_rate=0`, `429_count=0`, `5xx_count=0`, `p95_ms=297.22547`
- Proven 250 VU failure root cause before raising reserved concurrency:
  - with `ashmi-backend-dev-sg` reserved concurrency at `150`, k6 reported `5xx_count=1123`
  - the same test window showed API Gateway `5xx Sum=1123`
  - the same test window showed Lambda `Throttles Sum=1123`
  - Lambda `ConcurrentExecutions Maximum=150`, exactly matching the reserved concurrency cap
  - Lambda `Errors Sum=0`, and Lambda logs had no matching `ERROR`, `Exception`, or `Traceback`
  - therefore the root cause was Lambda reserved concurrency throttling, surfaced to the client as API Gateway `5xx`; it was not API Gateway rate/burst throttling because `429_count=0`
- Proven 500 VU confirmation failure root cause before raising reserved concurrency from `250` to `400`:
  - with `ashmi-backend-dev-sg` reserved concurrency at `250`, one 500 VU confirmation run reported `5xx_count=99`
  - the same test window showed Lambda `Throttles Sum=99`
  - Lambda `ConcurrentExecutions Maximum=250`, exactly matching the reserved concurrency cap
  - Lambda `Errors Sum=0`
  - after raising reserved concurrency to `400`, two subsequent 500 VU runs were clean with `http_req_failed_rate=0`, `429_count=0`, and `5xx_count=0`
- Current accepted SG dev ceiling:
  - `500` concurrent k6 virtual users for the public catalogue scenario
  - API Gateway `rate=2500`, `burst=5000`
  - Lambda account concurrency quota `1000`
  - backend Lambda reserved concurrency `400`
  - Neon Free plan
- Do not treat `2000` VUs as validated until separate clean test evidence exists.

### Verified checkout write-scale findings

- Module: Checkout writes and order creation.
- Test harness:
  - local pytest file: [backend/tests/integration/test_checkout_order_creation.py](C:/Ashmiwebportal/backend/tests/integration/test_checkout_order_creation.py)
  - this path is intentionally ignored by git in the current repo setup, so recreate/check the local test harness before relying on it in a fresh clone
  - default API target is the SG dev API Gateway base `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/api/v1`
- Completed stage results in `aws_dev`:
  - C1 25 VU checkout scale for 10 minutes passed: cart add/update, checkout summary, place order, pending payment state, order item/history writes, cart clear, and no 5xx/429
  - C3 100 VU limited-stock contention passed after switching to atomic stock reservation: with 30 available units, exactly 30 orders succeeded, remaining users were rejected cleanly, no oversell, no negative inventory, and no 5xx/429
  - C4 250 VU write-heavy checkout was accepted as application-behavior passed: a pytest run failed only because the small 4-variant `aws_dev` data set under-provisioned one SKU and returned a clean out-of-stock business error; no platform/system failure was identified from that result
  - C5 500 VU confirmation passed after batching setup at 50 concurrent users and synchronizing only `/checkout/place-order`: 500 successful pending orders, no 5xx/429, DB consistency checks passed, no negative inventory, and successful place-order p95 stayed below the configured 20 second threshold
- Checkout scale-test data notes:
  - `aws_dev` currently has a very small product/variant data set compared with the original plan expectation of hundreds of variants
  - for C4/C5 with only four active variants, replenish total available `product_variants.stock_quantity` before each run; atomic reservation decrements stock immediately for every successful pending order
  - stale C3/C4/C5 `inventory_reservations.status='held'` rows from old test runs should be reconciled before new runs; old pre-atomic held reservations did not necessarily deduct stock at creation time
  - C5 should not start all 500 users at login simultaneously; use controlled setup concurrency and release the synchronized load only for `/checkout/place-order`

## Known Operational Findings Carried Forward

### 1. Login / local confusion

- A local login failure is not always a bad password
- If Vite shows `socket hang up`, check backend health first
- If backend logs show startup DB errors, fix runtime mode / DB host before touching auth data

### 2. Admin dashboard latency in `aws_dev`

- The original Mumbai dev stack showed multi-second latency on admin/dashboard paths such as:
  - `auth/me`
  - `stats`
  - `revenue-trend`
  - `top-products`
- Backend/API latency mitigation has been applied by moving the dev backend/API direction to Singapore and reducing dashboard stats DB round trips in code.
- As of 2026-08-17, Singapore backend health is verified, but the latest local/feature-branch latency code is not proven deployed to `aws_dev`; `ashmi-backend-dev-sg` configuration inspected on 2026-08-17 showed `LastModified=2026-07-17T23:29:20Z`.
- Do not mark the latency issue resolved solely from `/health`; after a successful `develop` deployment, re-test dashboard timings for `auth/me`, `stats`, `revenue-trend`, and `top-products` before closing the latency task.

### 3. Revenue trend optimization work

Previously discussed safe manual plan:

- verify Neon SQL editor and Lambda hit the same logical DB
- run EXPLAIN ANALYZE for the actual query shape
- add timing instrumentation around service calls
- re-test after each change, not all at once

### 4. Manual UPI mode truth gap

From earlier validated handoff context:

- frontend exposes manual UPI ID and QR/app flow
- manual UPI ID path is not a true external collect-request implementation
- do not assume end-to-end real UPI collect behavior exists without re-validating code

## Key Documents In Repo

- Project handoff:
  - [PROJECT_HANDOFF_2026-04-15.md](C:/Ashmiwebportal/PROJECT_HANDOFF_2026-04-15.md)
- Production deployment runbook:
  - [PRODUCTION_DEPLOYMENT_RUNBOOK_2026-04-22.md](C:/Ashmiwebportal/PRODUCTION_DEPLOYMENT_RUNBOOK_2026-04-22.md)
- Current dev deploy workflow:
  - [.github/workflows/deploy-dev-v3.yml](C:/Ashmiwebportal/.github/workflows/deploy-dev-v3.yml)
- AWS dev module and 2,000-concurrent-user test plan:
  - [output/pdf/aws_dev_module_test_plan_2000_users.pdf](C:/Ashmiwebportal/output/pdf/aws_dev_module_test_plan_2000_users.pdf)
  - Created on 2026-08-17 after SG deployment and health check passed
  - Treat it as a test execution plan and evidence checklist, not proof that 2,000 concurrent users have already been validated

## Observability

- No repo-local Sentry SDK usage was confirmed in the currently reviewed frontend/backend source
- Accepted monitoring direction is AWS-native monitoring
- CloudWatch alarms and SNS notifications were validated in prior project work for `aws_dev`

## Production Direction

The agreed production direction in project work is:

- one AWS account
- separate IAM roles for dev and prod
- GitHub OIDC
- separate dev/prod resources
- validate fully in `aws_dev` before prod rollout

Resource direction already discussed:

- dev backend ECR:
  - `ashmi-backend-sg-dev`
- prod backend ECR:
  - `ashmi-backend-prod`
- dev Lambda:
  - `ashmi-backend-dev-sg`
- prod Lambda:
  - `ashmi-backend-prod`
- dev frontend bucket:
  - `ashmi-dev-frontend-sg`
- prod frontend bucket:
  - `ashmi-prod-frontend`

## Things Commonly Stale or Misleading

Always re-check these instead of trusting old chat memory:

1. deploy branch in workflow
2. whether DB URLs are synced by GitHub Actions or only set in Lambda
3. whether local testing is host-run or Docker-run
4. whether a login issue is auth-related or backend-health-related
5. whether a CloudWatch alert is a real persistent failure or a transient spike
6. whether backend code is resolving SSM `_PARAM` values or still expecting raw secrets

## TODO / Open Gaps

- Backend canonical automated test command is still not fully documented as a single source of truth
- Frontend canonical unit test script is still not established in `package.json`
- Alembic migration command is not yet documented as canonical
- Admin dashboard latency must be re-tested after the full Singapore dev stack cutover
- Neon region mismatch remains only for the legacy Mumbai app stack; target dev direction is full Singapore alignment
- Route-scoped Origin policy previously had a verified live-route gap on `POST /api/v1/admin/refunds`; current code now protects that route with `Depends(require_trusted_origin)`
- Route-scoped Origin policy currently has no repo-local automated tests under `backend/app/tests`
- 2,000-concurrent-user capacity is not yet proven; execute the PDF load-test plan and capture AWS/Neon evidence before claiming that capacity

## Current Blockers / Next Priorities

### Current `aws_dev` status

- GitHub Actions dev deployment is working from `develop`
- Frontend, backend, and image-processor deploy jobs have run successfully in recent `aws_dev` rollout work
- On 2026-08-17, `deploy-dev-v3.yml` completed successfully via manual workflow dispatch after correcting SG stack variables such as backend Lambda name, backend ECR repository, SG SSM parameter names, and runtime host settings
- Admin login and 2FA have worked in `aws_dev` during prior validation, but re-validation may still be needed after any auth or env change
- Singapore `aws_dev` backend/API path is built and `/dev/health` is verified healthy at `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/health`; latest recheck on 2026-08-17 IST returned `200 healthy`
- Current SG frontend is reachable at `https://db5l55bfhn85l.cloudfront.net`
- Latest local/feature-branch latency code still needs admin-dashboard timing validation before declaring latency resolved
- Current target direction: maintain a full Singapore dev stack, including `ashmi-dev-frontend-sg`, `ashmi-dev-assets-sg`, Singapore backend/API/Lambdas/ECR, SG SSM parameter names, and the dedicated SG CloudFront frontend distribution.
- Legacy Mumbai dev resources should remain only until SG validation/cutover is complete, then be deleted from AWS.

### Current blockers

1. Full functional validation is still incomplete even though deployment and health are green
   - frontend and backend smoke checks passed on the SG stack
   - live Razorpay payment, webhook processing, settlement visibility, and same-order payment re-attempt idempotency were manually validated on 2026-08-25 IST
   - admin image upload and product image processing were manually validated on 2026-08-30 IST
   - admin auth/2FA, dashboard latency, invoice, return/refund, privacy, and admin settings flows still need module-level re-testing against the live SG `aws_dev` stack
   - health success only proves startup/routing/config at smoke level, not full business workflow correctness

2. Local auth troubleshooting can still be confused by runtime mode mismatch
   - host-run backend and Docker backend must not be mixed during login testing

3. Prod rollout is not yet ready to execute automatically
   - prod IAM role exists
   - prod backend ECR/Lambda/S3/CloudFront direction has been planned
   - but final prod workflow, env sync completeness, and go-live validation remain incomplete

### Next safest priorities

1. Continue Singapore `aws_dev` migration validation
   - keep GitHub `aws_dev` variables and Lambda environment variables aligned to SG values
   - confirm CloudFront distribution `E3TY6IMS9QZRVN` and domain `db5l55bfhn85l.cloudfront.net` remain the active dev frontend target
   - re-test admin login
   - admin 2FA
   - `/health`
   - dashboard latency endpoints
   - image-processing callback path
   - forgot-password email link routes to CloudFront via `FRONTEND_URL`

2. Re-test `aws_dev` latency after SG cutover
   - current chosen direction is full app-resource alignment in `ap-southeast-1`, not moving Neon or adding RDS
   - compare dashboard endpoint latency after Singapore frontend/API/image cutover
   - add more service timing or DB indexes only if same-region latency remains high

3. Finalize prod deployment contract before rollout
   - confirm prod workflow trigger and approval gate
   - confirm prod env vars/secrets completeness
   - confirm prod Lambda runtime env strategy
   - confirm rollback image/tag procedure

4. Keep `aws_dev` as the proving ground
   - no prod rollout until `aws_dev` validation is stable for auth, dashboard, checkout path, email path, and monitoring
## Session Bootstrap Guidance

When starting a new session in this repo, assume the following until disproved:

1. Dev deploy path is GitHub Actions on push to `develop`
2. Target dev backend is `ashmi-backend-dev-sg`; legacy Mumbai backend `ashmi-backend-dev` is migration-only until deleted
3. Singapore backend health is verified at `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/health`; latest 2026-08-17 IST check returned `200 healthy`
4. Target direction is a full Singapore dev stack, including `ashmi-dev-frontend-sg`, `ashmi-dev-assets-sg`, SG backend/API/Lambdas/ECR, SG SSM parameters, and a dedicated SG CloudFront distribution
5. Mumbai-related AWS resources should be treated as legacy and deleted after Singapore migration validation/cutover
6. Local login issues should first be debugged as runtime-health issues before auth-data issues
7. Docker Compose is local-only and should never be treated as AWS runtime infrastructure
