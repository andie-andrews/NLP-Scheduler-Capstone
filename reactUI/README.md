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

Set `VITE_AI_ASSISTANT_URL` if you want AI chat responses from a backend endpoint.
