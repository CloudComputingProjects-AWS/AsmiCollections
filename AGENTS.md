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
- Checkout behavior:
  - `/cart` is public
  - `/checkout`, `/orders`, `/profile`, and `/addresses` are protected customer routes
  - unauthenticated customers are redirected to login before checkout
- Order placement flow:
  - checkout validates cart, stock, address, coupon, shipping fee, and total
  - backend creates `orders` and `order_items` records in Neon
  - initial payment status is `pending`
  - payment gateway confirmation, polling, or webhook updates payment/order status
  - successful payment should move payment status to `paid` and order status toward confirmed/fulfillment flow

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
- Singapore frontend S3 bucket for full SG dev stack:
  - `ashmi-dev-frontend-sg`
- Singapore assets S3 bucket:
  - `ashmi-dev-assets-sg`
- Singapore CloudFront distribution:
  - create/configure a dedicated SG dev distribution, then store its distribution ID in GitHub `aws_dev` as `CLOUDFRONT_DISTRIBUTION_ID`
  - the distribution should use `ashmi-dev-frontend-sg` as the frontend origin
  - the public CloudFront domain must become the `FRONTEND_URL` value for SG validation
  - `IMAGE_CDN_DOMAIN` should use the SG CloudFront domain if the same distribution exposes `uploads/processed/...`, otherwise use the selected SG assets CDN domain
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

- Current project direction is to keep `SameSite=Strict` for browser auth cookies
- Because `SameSite=Strict` is being kept, browser-driven state-changing routes should also enforce strict `Origin` validation
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
  - burst: `10`
  - rate: `5`
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

## Current Blockers / Next Priorities

### Current `aws_dev` status

- GitHub Actions dev deployment is working from `develop`
- Frontend, backend, and image-processor deploy jobs have run successfully in recent `aws_dev` rollout work
- Admin login and 2FA have worked in `aws_dev` during prior validation, but re-validation may still be needed after any auth or env change
- Singapore `aws_dev` backend/API path is built and `/dev/health` is verified healthy at `https://r5k4xtwcpi.execute-api.ap-southeast-1.amazonaws.com/dev/health`; latest recheck on 2026-08-17 IST returned `200 healthy`
- Latest local/feature-branch latency code is not confirmed deployed to `aws_dev`; confirm a successful `develop` workflow run and deployed Lambda image/update before declaring latency resolved
- Current target direction: maintain a full Singapore dev stack, including `ashmi-dev-frontend-sg`, `ashmi-dev-assets-sg`, Singapore backend/API/Lambdas/ECR, SG SSM parameter names, and a dedicated SG CloudFront frontend distribution.
- Legacy Mumbai dev resources should remain only until SG validation/cutover is complete, then be deleted from AWS.

### Current blockers

1. Full Singapore `aws_dev` stack consistency is not yet complete
   - backend/API health is validated in Singapore
   - latest code deployment to `aws_dev` is not confirmed by the 2026-08-17 checks; the backend Lambda `LastModified` value still needed comparison against the latest successful GitHub Actions run
   - frontend bucket, SG CloudFront distribution, image pipeline wiring, and GitHub `aws_dev` variables/secrets still need to be aligned to the SG stack
   - after cutover, validate admin auth/dashboard latency before further optimization

2. Local auth troubleshooting can still be confused by runtime mode mismatch
   - host-run backend and Docker backend must not be mixed during login testing

3. Prod rollout is not yet ready to execute automatically
   - prod IAM role exists
   - prod backend ECR/Lambda/S3/CloudFront direction has been planned
   - but final prod workflow, env sync completeness, and go-live validation remain incomplete

### Next safest priorities

1. Continue Singapore `aws_dev` migration validation
   - create/configure `ashmi-dev-frontend-sg`
   - create/configure dedicated SG CloudFront distribution and point `FRONTEND_URL`, `CORS_ORIGINS`, and `IMAGE_CDN_DOMAIN` at its domain as appropriate
   - update/create Singapore image processor Lambda and callback URL
   - wire Singapore S3 image trigger and processed asset path
   - update GitHub `aws_dev` variables/secrets for the full SG stack only after manual Singapore validation is complete
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
