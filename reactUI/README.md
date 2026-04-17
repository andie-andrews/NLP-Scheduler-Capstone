# React UI (Parity Port of Streamlit App)

This folder contains a React + TypeScript recreation of the Python Streamlit UI.

## Features mirrored
- Login with JWT claim extraction
- Role-aware navigation
- My Schedule weekly view
- Manage Employees (search/create/edit/delete)
- Manage Schedules overview with weekly totals and schedule CRUD
- AI Assistant chat shell with pluggable endpoint

## Run
```bash
cd reactUI
cp .env.example .env
npm install
npm run dev
```

## Environment variables

### `VITE_SCHEDULER_API_BASE_URL`
Base URL for the Scheduler REST API used by regular app features (login, employees, schedules, shifts).

Example:
- `https://localhost:7259` for local API
- `https://<deployed-api-domain>` for deployed API

### `VITE_AI_ASSISTANT_URL`
URL for the AI assistant backend endpoint that the React chat UI calls.

This is **not** the Scheduler API base URL. It should point to an endpoint that accepts a chat payload (for example, a backend route that wraps the Python orchestrator and returns a response summary).

Examples:
- `http://localhost:8000/api/assistant/chat`
- `https://<assistant-service-domain>/api/assistant/chat`

## Where to put the OpenAI key
Do **not** put your OpenAI API key in `reactUI/.env` (anything prefixed with `VITE_` is exposed to the browser).

Instead, put `OPENAI_API_KEY` in the backend environment (for this repo, use `app/.env` based on `app/.env.example`). The assistant backend should read that key server-side and the React UI should only call your backend assistant URL.
