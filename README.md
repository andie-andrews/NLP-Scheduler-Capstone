# NLP Scheduler Capstone

This repository contains an end-to-end workforce scheduling system with both traditional UI workflows and AI-assisted natural-language scheduling.

> Looking for the original capstone proposal content? See `docs/capstone_proposal.md`.

## Project overview

The project combines:

- A **.NET 8 Scheduler API** for auth, employees, schedules, and shifts.
- A **Streamlit app** for role-based scheduling workflows and assistant UI.
- A **FastAPI assistant backend** used by the React chat interface.
- A **React + TypeScript app** (Vite) that mirrors the core management workflows.
- A Python **LLM orchestration layer** that turns natural-language requests into API calls.

## Architecture

### Components

1. **Scheduler API** (`apis/Scheduler.Api/Scheduler.Api`)
   - ASP.NET Core (`net8.0`), JWT Bearer auth
   - Dapper + SQL Server
   - Swagger/OpenAPI enabled

2. **Streamlit frontend** (`app/main.py`)
   - Login, schedules, employees, assistant pages
   - Uses `app/api_client.py` for API calls

3. **Assistant backend** (`app/assistant_api.py`)
   - FastAPI endpoint for React assistant chat
   - Calls the same orchestrator used by Streamlit

4. **React frontend** (`reactUI`)
   - React 18 + TypeScript + Vite
   - Uses Scheduler API + assistant backend endpoints

5. **Orchestration layer** (`app/llm`)
   - Intent parsing, flow orchestration, context resolution
   - OpenAPI tooling and API operation execution

### Runtime flow

- **Core CRUD flow:** Frontends authenticate with Scheduler API and send JWT-authenticated requests.
- **Streamlit assistant flow:** Streamlit invokes the orchestrator in-process.
- **React assistant flow:** React calls FastAPI `/api/assistant/chat`, which invokes the orchestrator.

## Tech stack

- **Backend/API:** .NET 8, ASP.NET Core, Dapper, Microsoft.Data.SqlClient, Swashbuckle
- **Python apps/services:** Python 3.11+, Streamlit, FastAPI, Uvicorn, LangChain, OpenAI SDK
- **Frontend:** React 18, TypeScript 5, Vite 5, Node 18.18+

## Repository layout

```text
apis/
  Scheduler.Api/
    Scheduler.Api/        # ASP.NET Core API
app/
  main.py                 # Streamlit entrypoint
  assistant_api.py        # FastAPI assistant backend
  llm/                    # orchestration/tooling
reactUI/
  src/                    # React frontend
tests/                    # Python tests
docs/
  capstone_proposal.md    # Original capstone proposal (moved from old README)
```

---

## Local setup

### Prerequisites

- Git
- .NET SDK 8.x
- SQL Server (local or reachable)
- Node.js 18.18+ + npm
- Python 3.11+
- VS Code (recommended)

### VS Code + Python setup

1. Install Python 3.11+.
2. Install VS Code extensions:
   - Python (Microsoft)
   - Pylance (Microsoft)
3. In `app/`, create and activate a virtual environment:

```bash
cd app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. In VS Code, run **Python: Select Interpreter** and choose `app/.venv`.

### Environment variables

#### Python (`app/.env`)

```bash
cd app
cp .env.example .env
```

Set at minimum:

- `SCHEDULER_API_BASE_URL=https://localhost:7259`
- `SCHEDULER_API_VERIFY_SSL=false` (for local self-signed certs)
- `OPENAI_API_KEY=...`

#### React (`reactUI/.env`)

```bash
cd reactUI
cp .env.example .env
```

Set at minimum:

- `VITE_SCHEDULER_API_BASE_URL=https://localhost:7259`
- `VITE_AI_ASSISTANT_URL=http://localhost:8000/api/assistant/chat`

### Run services

#### 1) Scheduler API

```bash
cd apis/Scheduler.Api/Scheduler.Api
dotnet restore
dotnet run
```

If needed, trust local ASP.NET cert:

```bash
dotnet dev-certs https --trust
```

#### 2) Assistant backend (FastAPI)

```bash
cd app
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn assistant_api:app --reload --port 8000
```

Optional health check:

```bash
curl http://localhost:8000/health
```

#### 3) Streamlit app

```bash
cd app
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
streamlit run main.py
```

#### 4) React app

```bash
cd reactUI
npm install
cp .env.example .env
npm run dev
```

### Recommended startup order

1. Scheduler API
2. FastAPI assistant backend (for React assistant)
3. Streamlit and/or React frontend

### Tests

From repo root:

```bash
pytest
```
