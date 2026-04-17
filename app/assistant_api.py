"""HTTP backend for the in-repo assistant orchestrator.

This mirrors the Streamlit assistant behavior by keeping conversation state server-side
and calling the same `run_orchestrator(...)` function used by the Streamlit UI.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm.memory import ConversationMemory
from llm.orchestrator import run_orchestrator


@dataclass
class AuthUser:
    role: str | None
    employee_id: int | None
    token: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversationId: str | None = None


class ChatResponse(BaseModel):
    conversationId: str
    response: Any


class SessionRecord(BaseModel):
    session: dict[str, Any]
    last_seen_epoch_seconds: float


app = FastAPI(title="Scheduler Assistant API", version="1.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ASSISTANT_API_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation sessions for parity with Streamlit session state.
conversation_store: dict[str, SessionRecord] = {}
session_ttl_seconds = int(os.getenv("ASSISTANT_SESSION_TTL_SECONDS", str(60 * 60 * 8)))


def _cleanup_expired_sessions() -> None:
    now = time.time()
    expired = [
        conversation_id
        for conversation_id, record in conversation_store.items()
        if now - record.last_seen_epoch_seconds > session_ttl_seconds
    ]
    for conversation_id in expired:
        conversation_store.pop(conversation_id, None)


def _decode_bearer_token(authorization: str | None) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid Bearer token")

    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"Unable to decode token: {exc}") from exc

    employee_id_value = claims.get("employeeId")
    employee_id = int(employee_id_value) if employee_id_value is not None else None

    return AuthUser(
        role=claims.get("role"),
        employee_id=employee_id,
        token=token,
    )


def _get_or_create_session(conversation_id: str, user: AuthUser) -> dict[str, Any]:
    if conversation_id not in conversation_store:
        conversation_store[conversation_id] = SessionRecord(
            session={
                "memory": ConversationMemory(),
                "role": user.role,
                "employee_id": user.employee_id,
            },
            last_seen_epoch_seconds=time.time(),
        )

    record = conversation_store[conversation_id]
    record.last_seen_epoch_seconds = time.time()

    session = record.session
    session["role"] = user.role
    session["employee_id"] = user.employee_id
    return session


@app.get("/health")
def healthcheck() -> dict[str, Any]:
    _cleanup_expired_sessions()
    return {
        "status": "ok",
        "activeConversations": len(conversation_store),
        "sessionTtlSeconds": session_ttl_seconds,
    }


@app.post("/api/assistant/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    _cleanup_expired_sessions()
    user = _decode_bearer_token(authorization)

    conversation_id = payload.conversationId or str(uuid.uuid4())
    session = _get_or_create_session(conversation_id, user)

    response = run_orchestrator(
        message=payload.message,
        token=user.token,
        session=session,
    )

    return ChatResponse(conversationId=conversation_id, response=response)


@app.delete("/api/assistant/chat/{conversation_id}")
def reset_chat(conversation_id: str, authorization: str | None = Header(default=None)) -> dict[str, str]:
    _decode_bearer_token(authorization)
    conversation_store.pop(conversation_id, None)
    return {"status": "cleared"}
