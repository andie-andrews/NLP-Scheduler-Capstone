# React AI Assistant Backend

This project now includes a Python HTTP backend (`app/assistant_api.py`) that wraps the same orchestrator used by the Streamlit app.

## Why this exists

- Streamlit calls `run_orchestrator(...)` in-process.
- React runs in the browser and cannot safely call OpenAI directly.
- The backend endpoint keeps chat state server-side and forwards requests to the orchestrator.

## Endpoints

- `GET /health`
- `POST /api/assistant/chat`
  - body: `{ "message": "...", "conversationId": "optional" }`
  - returns: `{ "conversationId": "...", "response": <orchestrator-response> }`
- `DELETE /api/assistant/chat/{conversationId}`

## Local run

```bash
cd app
cp .env.example .env
pip install -r requirements.txt
uvicorn assistant_api:app --reload --port 8000
```

> `assistant_api.py` and the orchestrator now load `.env` automatically (`app/.env` first, then repo-root `.env`), so `OPENAI_API_KEY` is picked up even if the process is started from a different working directory.

- `OPENAI_API_KEY` (in `app/.env`)
- `SCHEDULER_API_BASE_URL` / `EMPLOYEE_API_BASE_URL` / `SCHEDULER_API_VERIFY_SSL`

## Optional environment

- `ASSISTANT_API_ALLOW_ORIGINS` (default `*`)
- `ASSISTANT_SESSION_TTL_SECONDS` (default `28800`, 8 hours)
