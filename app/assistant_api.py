import os
import uuid
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm.memory import ConversationMemory
from llm.orchestrator import run_orchestrator


@dataclass
class AuthUser:
    role: str | None
    employee_id: int | None
    token: str


class ChatRequest(BaseModel):
    message: str
    conversationId: str | None = None


class ChatResponse(BaseModel):
    conversationId: str
    response: Any


app = FastAPI(title="Scheduler Assistant API", version="1.0.0")

allowed_origins = [origin.strip() for origin in os.getenv("ASSISTANT_API_ALLOW_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation sessions for parity with Streamlit session state.
conversation_store: dict[str, dict[str, Any]] = {}


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
        conversation_store[conversation_id] = {
            "memory": ConversationMemory(),
            "role": user.role,
            "employee_id": user.employee_id,
        }

    session = conversation_store[conversation_id]
    session["role"] = user.role
    session["employee_id"] = user.employee_id
    return session


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/assistant/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
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
