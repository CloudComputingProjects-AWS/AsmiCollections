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
- Current known latency caveat:
  - AWS app resources are in `ap-south-1`
  - Neon database has been observed in `ap-southeast-1`
  - this cross-region path is a known source of latency

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

These names were established during the project rollout work and should be treated as the current dev baseline unless AWS has changed later.

### IAM / OIDC

- GitHub OIDC provider exists in the single AWS account
- Dev deploy role:
  - `GitHubActions-Ashmiwebportal-Deploy-Dev`
- Prod deploy role:
  - `GitHubActions-Ashmiwebportal-Deploy-Prod`

### Dev compute and storage

- Backend ECR repository:
  - `ashmi-backend`
- Image processor ECR repository:
  - `ashmi-image-processor`
- Backend Lambda:
  - `ashmi-backend-dev`
- Image processor Lambda:
  - `ashmi-image-processor-dev`
- Frontend S3 bucket:
  - `ashmi-dev-frontend`
- Additional dev assets bucket used in the project:
  - `ashmi-dev-assets`
- Dev CloudFront distribution ID:
  - `E32QTT8QPXCW64`
- Current dev frontend domain observed in project work:
  - `di156w1uc1xwk.cloudfront.net`

## GitHub Environment Contract

### `aws_dev` variables currently expected by workflow

- `APP_NAME`
- `APP_VERSION`
- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME`
- `CLOUDFRONT_DISTRIBUTION_ID`
- `ECR_REPOSITORY`
- `ENVIRONMENT`
- `FRONTEND_URL`
- `IMAGE_CDN_DOMAIN`
- `IMAGE_PROCESSOR_ECR_REPOSITORY`
- `IMAGE_PROCESSOR_LAMBDA_FUNCTION_NAME`
- `JWT_ALGORITHM`
- `LAMBDA_FUNCTION_NAME`
- `S3_FRONTEND_BUCKET`

### `aws_dev` secrets currently expected by workflow

- `DATABASE_URL`
- `DATABASE_URL_SYNC`
- `IMAGE_CALLBACK_SECRET`
- `VITE_API_URL`

### Backend Lambda runtime settings synced by workflow

As of the current verified workflow, [deploy-dev-v3.yml](C:/Ashmiwebportal/.github/workflows/deploy-dev-v3.yml) syncs these backend Lambda runtime settings automatically:

- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT`
- `FRONTEND_URL`
- `JWT_ALGORITHM`
- `DATABASE_URL`
- `DATABASE_URL_SYNC`
- `IMAGE_CALLBACK_SECRET`

Therefore, `DATABASE_URL`, `DATABASE_URL_SYNC`, and `FRONTEND_URL` should be maintained in GitHub `aws_dev` and are pushed into `ashmi-backend-dev` during deploy.

## Backend Runtime Configuration Truths

### Config file intent

- [backend/app/core/config.py](C:/Ashmiwebportal/backend/app/core/config.py) is intentionally being used as a schema/defaults definition layer
- Sensitive runtime values should come from environment variables, not hard-coded secrets in the file
- The user previously chose to keep some values blank in code and source them from environment/runtime configuration

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

### Neon connection guidance

- Current backend DB code uses `asyncpg` with `NullPool` for `aws_dev` / `production`
- For the current code path, use the direct Neon host for backend runtime URLs, not the `-pooler` host
- `DATABASE_URL` should use the async SQLAlchemy driver format:
  - `postgresql+asyncpg://USER:PASSWORD@DIRECT_NEON_HOST/DB_NAME`
- `DATABASE_URL_SYNC` should use the sync migration driver format:
  - `postgresql+psycopg2://USER:PASSWORD@DIRECT_NEON_HOST/DB_NAME?sslmode=require`
- If Neon shows a pooled host like `ep-xxx-pooler...`, remove `-pooler` or turn connection pooling off in the Neon connection modal to get the direct host
- Cross-region latency is a known concern and has been discussed as a future architecture improvement

## Current Deployment Workflow Behavior

The current dev workflow has three jobs:

1. `deploy-image-processor`
2. `deploy-backend`
3. `deploy-frontend`

Important details:

- `deploy-backend` depends on `deploy-image-processor`
- image processor config is synced before image deployment
- backend Lambda config is synced before backend image deployment
- frontend build uses `VITE_API_URL`
- frontend artifacts are uploaded to S3 and then CloudFront is invalidated

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
- `aws_dev` should set `FRONTEND_URL` to:
  - `https://di156w1uc1xwk.cloudfront.net`
- Reset links should therefore route to:
  - local: `http://localhost:3000/reset-password?token=...`
  - `aws_dev`: `https://di156w1uc1xwk.cloudfront.net/reset-password?token=...`

### 2FA

- Admin 2FA has worked in `aws_dev` during previous validation
- TOTP failures can still occur if:
  - the wrong authenticator secret is being used
  - the code expires
  - the device clock is off

### Rate limiting architecture

Current project direction is AWS-side protection, not app-side Redis middleware.

- `RateLimitMiddleware` is intentionally not active
- Redis-based app rate limiter was removed from active architecture
- Current protection depends on:
  - API Gateway throttling
  - WAF rate-based rules
  - managed WAF protections
  - application validation/auth logic

### Verified `aws_dev` protection baseline

- API ID:
  - `9amq4q9qa4`
- CloudFront distribution:
  - `E32QTT8QPXCW64`
- WAF protections previously verified:
  - rate-based block rule
  - AWS managed IP reputation
  - AWS managed common rules
  - AWS managed known bad inputs

## Known Operational Findings Carried Forward

### 1. Login / local confusion

- A local login failure is not always a bad password
- If Vite shows `socket hang up`, check backend health first
- If backend logs show startup DB errors, fix runtime mode / DB host before touching auth data

### 2. Admin dashboard latency in `aws_dev`

- Admin dashboard endpoints such as:
  - `auth/me`
  - `stats`
  - `revenue-trend`
  - `top-products`
  have shown multi-second latency in `aws_dev`
- EXPLAIN ANALYZE for the tested `revenue-trend` query in Neon SQL editor showed a fast query by itself
- Therefore the full latency is not explained by raw SQL execution alone
- Cross-region network overhead between AWS `ap-south-1` and Neon `ap-southeast-1` remains a prime suspect

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
  - `ashmi-backend`
- prod backend ECR:
  - `ashmi-backend-prod`
- dev Lambda:
  - `ashmi-backend-dev`
- prod Lambda:
  - `ashmi-backend-prod`
- dev frontend bucket:
  - `ashmi-dev-frontend`
- prod frontend bucket:
  - `ashmi-prod-frontend`

## Things Commonly Stale or Misleading

Always re-check these instead of trusting old chat memory:

1. deploy branch in workflow
2. whether DB URLs are synced by GitHub Actions or only set in Lambda
3. whether local testing is host-run or Docker-run
4. whether a login issue is auth-related or backend-health-related
5. whether a CloudWatch alert is a real persistent failure or a transient spike

## TODO / Open Gaps

- Backend canonical automated test command is still not fully documented as a single source of truth
- Frontend canonical unit test script is still not established in `package.json`
- Alembic migration command is not yet documented as canonical
- Admin dashboard latency remains an open optimization track
- Neon region mismatch remains unresolved

## Current Blockers / Next Priorities

### Current `aws_dev` status

- GitHub Actions dev deployment is working from `develop`
- Frontend, backend, and image-processor deploy jobs have run successfully in recent `aws_dev` rollout work
- Admin login and 2FA have worked in `aws_dev` during prior validation, but re-validation may still be needed after any auth or env change
- `aws_dev` backend currently depends on Neon PostgreSQL over a remote network path

### Current blockers

1. `aws_dev` latency remains an open issue
   - admin dashboard endpoints have shown multi-second response times
   - cross-region traffic between AWS `ap-south-1` and Neon `ap-southeast-1` remains the leading known suspect

2. Local auth troubleshooting can still be confused by runtime mode mismatch
   - host-run backend and Docker backend must not be mixed during login testing

3. Prod rollout is not yet ready to execute automatically
   - prod IAM role exists
   - prod backend ECR/Lambda/S3/CloudFront direction has been planned
   - but final prod workflow, env sync completeness, and go-live validation remain incomplete

### Next safest priorities

1. Re-test `aws_dev` with stable runtime config
   - admin login
   - admin 2FA
   - `/health`
   - dashboard latency endpoints
   - image-processing callback path
   - forgot-password email link routes to CloudFront via `FRONTEND_URL`

2. Resolve or reduce `aws_dev` latency
   - verify pooled/direct Neon host choice
   - add service timing around slow endpoints
   - decide whether to move DB region or app region for long-term fix

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
2. AWS dev backend is `ashmi-backend-dev`
3. AWS dev frontend is behind CloudFront `E32QTT8QPXCW64`
4. Local login issues should first be debugged as runtime-health issues before auth-data issues
5. Docker Compose is local-only and should never be treated as AWS runtime infrastructure



