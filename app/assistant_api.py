"""HTTP backend for the in-repo assistant orchestrator.

Exposes both:
- legacy v1 assistant routes under `/api/assistant/*`
- v2 assistant routes mounted from `app/api/routes.py` under `/api/v2/assistant/*`

Both paths use centralized orchestration/session infrastructure.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.routes import router as assistant_v2_router
from api.session_store import (
    cleanup_expired_sessions,
    conversation_store,
    decode_bearer_token,
    get_or_create_session,
    session_ttl_seconds,
)
from llm.domain_orchestration.engine import run_orchestration_request


class ChatRequest(BaseModel):
    """Legacy v1 assistant chat request payload."""

    message: str = Field(min_length=1)
    conversationId: str | None = None


class ChatResponse(BaseModel):
    """Legacy v1 assistant chat response payload."""

    conversationId: str
    response: Any


app = FastAPI(title="Scheduler Assistant API", version="1.1.0")
LEGACY_V1_APPCODE = "scheduling"
V2_ROUTE_PREFIX = "/api/v2/assistant"

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ASSISTANT_API_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,https://localhost:5173,https://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if origin.strip()
]

allow_all_origins = any(origin == "*" for origin in allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allowed_origins,
    # Browsers block credentialed CORS when wildcard origin is used.
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, Any]:
    cleanup_expired_sessions()
    return {
        "status": "ok",
        "activeConversations": len(conversation_store),
        "sessionTtlSeconds": session_ttl_seconds,
    }


@app.post("/api/assistant/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    cleanup_expired_sessions()
    user = decode_bearer_token(authorization)

    conversation_id = payload.conversationId or str(uuid.uuid4())
    session = get_or_create_session(conversation_id, user)

    response = run_orchestration_request(
        appcode=LEGACY_V1_APPCODE,
        message=payload.message,
        token=user.token,
        session=session,
        role=session.get("role"),
    )

    return ChatResponse(conversationId=conversation_id, response=response)


@app.delete("/api/assistant/chat/{conversation_id}")
def reset_chat(conversation_id: str, authorization: str | None = Header(default=None)) -> dict[str, str]:
    decode_bearer_token(authorization)
    conversation_store.pop(conversation_id, None)
    return {"status": "cleared"}



# Mount v2 assistant routes from `app/api/routes.py` (prefix: /api/v2/assistant).
app.include_router(assistant_v2_router)
