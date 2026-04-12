# AGENTS.md

## Repo workflows

- Local stack from the repo root uses Docker Compose for Postgres, Redis, and the FastAPI API: `docker compose up postgres redis api`
- Frontend work happens in `frontend/` with Vite scripts from `package.json`:
  - `npm run dev`
  - `npm run build`
  - `npm run lint`
  - `npm run preview`
- Frontend Vite dev server proxies `/api` requests to `http://localhost:8000` per `frontend/vite.config.js`
- Frontend end-to-end specs live under `frontend/src/tests/e2e/`; Playwright is configured in `frontend/playwright.config.js` and runs against the Vite dev server on port `3000`: `npx playwright test`
- Backend local API entrypoint is `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` from `backend/`

## Deployment workflow

- `.github/workflows/deploy-dev-v3.yml` deploys on push to `main`
- Backend deploy builds `backend/Dockerfile.lambda`, pushes the image to ECR, updates the Lambda function, then waits for the function update to complete
- Frontend deploy runs `npm ci` and `npm run build` in `frontend/` on Node.js `20`, syncs `dist/` to S3, and invalidates CloudFront via `CLOUDFRONT_DISTRIBUTION_ID`
- Current frontend build-time env used by the deploy workflow: `VITE_API_URL`

## Observability

- No repo-local Sentry SDK usage was found in current `frontend/src` or `backend/app` source; confirm instrumentation before documenting Sentry envs here again

## TODO

- Backend test command needs confirmation before documenting as canonical: `backend/pytest.ini.toml` points to `tests/`, but `backend/app/tests/test_payment_service.py` currently documents `pytest app/tests/test_payment_service.py -v` and marks it as not runtime-verified
- Frontend has unit tests under `frontend/src/tests/unit/`; `frontend/src/tests/unit/validations.test.js` documents `npx vitest run src/tests/unit/validations.test.js`, but `frontend/package.json` does not define a canonical test script yet
- Backend includes Alembic config in `backend/alembic.ini` and `backend/migrations/`, but a canonical migration command is not documented yet
