# Deploying This Project to Production via GitHub

Short answer: **yes, you can deploy this through GitHub fairly easily** using GitHub Actions + a hosting platform.

Because this repo has two deployable pieces, treat them separately:

1. **`apis/Scheduler.Api`** (.NET Web API)
2. **`app/`** (Streamlit frontend + LLM orchestration)

## What to fix before production deployment

This project currently defaults to localhost URLs and disabled SSL verification for API calls.

Before deploying, configure runtime environment variables:

- `SCHEDULER_API_BASE_URL` (`https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net`)
- `SCHEDULER_API_VERIFY_SSL` (`true` in production)
- `ConnectionStrings__Default` (API DB connection string)
- `Jwt__Key` (API JWT signing key)
- `Jwt__Issuer` (API JWT issuer)

These are now supported by the Python client/orchestrator code.
The API now validates that `ConnectionStrings:Default`, `Jwt:Key`, and `Jwt:Issuer` are set at startup, so each new environment should define these values (through env vars, secret stores, or environment-specific appsettings files).

## Easiest deployment path from GitHub

## Option A (recommended for speed):

- **API** → Azure App Service (or Render Web Service) via GitHub Actions
- **Streamlit app** → Streamlit Community Cloud / Render / Azure Container Apps
- **Database** → managed SQL instance (Azure SQL / Neon / Supabase Postgres if migrated)

This is usually the least friction if you want something online quickly.

## Step-by-step rollout

### Local vs production configuration

Use `.env` locally (loaded by `app/main.py`) and host environment variables in production. Create `app/.env` locally (it is git-ignored), for example by copying `app/.env.example`.

**Local development (`app/.env`)**

- `SCHEDULER_API_BASE_URL=http://localhost/schedulerapi`
- `EMPLOYEE_API_BASE_URL=http://localhost/employeeapi`
- `SCHEDULER_API_VERIFY_SSL=false`

You can copy from `app/.env.example` and adjust as needed.

**Production deployment values**

- `SCHEDULER_API_BASE_URL=https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net/`
- `SCHEDULER_API_VERIFY_SSL=true`

For Azure App Service (Streamlit host), set these under **Environment variables** and restart the app.
For Streamlit Community Cloud, set the same keys in **Advanced settings → Secrets** (or in `secrets.toml`).


### 1) Prepare secrets in GitHub

In **GitHub → Settings → Secrets and variables → Actions**, add:

- `OPENAI_API_KEY`
- `SCHEDULER_API_BASE_URL`
- API deployment secrets (platform-specific)
- DB connection string secret for API
- JWT secrets used by `Scheduler.Api`

### 2) Add CI checks on push/PR

At minimum:

- Python tests: `pytest`
- .NET build/test for `Scheduler.Api`
- Optional linting

Gate production deployment on passing checks.

### 3) Add API CD workflow

Trigger on `main` branch merge:

- restore/build/publish .NET API
- deploy artifact to your target host
- run a smoke check against `/health`

### 4) Add Streamlit CD workflow

Deploy `app/` with env vars:

- `OPENAI_API_KEY`
- `SCHEDULER_API_BASE_URL` (the public API URL)
- `SCHEDULER_API_VERIFY_SSL=true`

### 5) Validate cross-service auth/network

- Streamlit can reach API over HTTPS
- JWT issuer/key env vars in API are correct
- CORS is configured if browser-origin calls require it

### 6) Add a safe production profile

Use separate production settings and never reuse local dev defaults.

## Why this helps before MCP

Deploying first gives you:

- a stable URL surface for MCP server/tool integration
- realistic latency/error behavior
- production auth patterns to propagate into MCP
- operational confidence before adding a new protocol layer

## Suggested order (practical)

1. Deploy API to production-like environment.
2. Deploy Streamlit app with env-based API URL.
3. Add monitoring + smoke tests.
4. Then start MCP integration in phases.
