"""HTTP backend for the in-repo assistant orchestrator.

This mirrors the Streamlit assistant behavior by keeping conversation state server-side
and calling the same `run_orchestrator(...)` function used by the Streamlit UI.
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
from llm.orchestrator import run_orchestrator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversationId: str | None = None


class ChatResponse(BaseModel):
    conversationId: str
    response: Any


app = FastAPI(title="Scheduler Assistant API", version="1.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ASSISTANT_API_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
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

    response = run_orchestrator(
        message=payload.message,
        token=user.token,
        session=session,
    )

    return ChatResponse(conversationId=conversation_id, response=response)


@app.delete("/api/assistant/chat/{conversation_id}")
def reset_chat(conversation_id: str, authorization: str | None = Header(default=None)) -> dict[str, str]:
    decode_bearer_token(authorization)
    conversation_store.pop(conversation_id, None)
    return {"status": "cleared"}


app.include_router(assistant_v2_router)
