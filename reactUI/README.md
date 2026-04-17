# React UI (Parity Port of Streamlit App)

This folder contains a React + TypeScript recreation of the Python Streamlit UI.

## Features mirrored
- Login with JWT claim extraction
- Role-aware navigation
- My Schedule weekly view
- Manage Employees (search/create/edit/delete)
- Manage Schedules overview with weekly totals and schedule CRUD
- AI Assistant chat shell backed by the Python orchestrator API

## Run React UI
```bash
cd reactUI
cp .env.example .env
npm install
npm run dev
```

## Run assistant backend (for chat parity)
The Streamlit app calls the orchestrator directly in-process. The React app needs an HTTP endpoint, which this repo now provides at `app/assistant_api.py`.

Detailed backend notes: `docs/react_assistant_backend.md`.

```bash
cd app
cp .env.example .env
pip install -r requirements.txt
uvicorn assistant_api:app --reload --port 8000
```

Then set in `reactUI/.env`:

```env
VITE_AI_ASSISTANT_URL=http://localhost:8000/api/assistant/chat
```

## Environment variables

### `VITE_SCHEDULER_API_BASE_URL`
Base URL for the Scheduler REST API used by regular app features (login, employees, schedules, shifts).

### `VITE_AI_ASSISTANT_URL`
URL for the AI assistant backend endpoint that the React chat UI calls. This should point to `/api/assistant/chat` on the assistant backend.

## Where to put the OpenAI key
Do **not** put your OpenAI API key in `reactUI/.env` (anything prefixed with `VITE_` is exposed to the browser).

Put `OPENAI_API_KEY` in `app/.env` (server-side). The backend endpoint uses that key when the orchestrator calls OpenAI.


## Troubleshooting

### `TypeError: crypto.getRandomValues is not a function`
This usually means Node is too old or does not expose Web Crypto correctly.

1. Use Node 18.18+ (recommended: Node 20 LTS).
2. Reinstall dependencies after switching Node:

```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

The Vite config also includes a compatibility fallback that assigns `globalThis.crypto` from `node:crypto.webcrypto` when needed.
