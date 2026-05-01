from __future__ import annotations

import os
import hashlib
import time
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import HTTPException
from pydantic import BaseModel

from llm.memory import ConversationMemory


@dataclass
class AuthUser:
    """Decoded bearer-token user context used for session bootstrap."""

    role: str | None
    employee_id: int | None
    token: str


class SessionRecord(BaseModel):
    """Container for conversation session state and last-seen timestamp."""

    session: dict[str, Any]
    last_seen_epoch_seconds: float


conversation_store: dict[str, SessionRecord] = {}
session_ttl_seconds = int(os.getenv("ASSISTANT_SESSION_TTL_SECONDS", str(60 * 60 * 8)))


def cleanup_expired_sessions() -> None:
    now = time.time()
    expired = [
        conversation_id
        for conversation_id, record in conversation_store.items()
        if now - record.last_seen_epoch_seconds > session_ttl_seconds
    ]
    for conversation_id in expired:
        conversation_store.pop(conversation_id, None)


def decode_bearer_token(authorization: str | None) -> AuthUser:
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


def get_or_create_session(conversation_id: str, user: AuthUser) -> dict[str, Any]:
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


def default_conversation_id_for_user(user: AuthUser) -> str:
    """Build a stable per-user fallback conversation id for multi-turn continuity.

    Used when the client does not send `conversationId`.
    """
    if user.employee_id is not None:
        return f"user:{user.employee_id}"
    token_fingerprint = hashlib.sha256(user.token.encode("utf-8")).hexdigest()[:16]
    return f"token:{token_fingerprint}"
