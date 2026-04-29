from __future__ import annotations

import uuid

from fastapi import APIRouter, Header, HTTPException

from api.request_models import AssistantRequest, AssistantResponse
from api.session_store import cleanup_expired_sessions, conversation_store, decode_bearer_token, get_or_create_session
from orchestration.appcode_resolver import AppcodeResolutionError
from orchestration.domain_router import DomainRoutingError
from orchestration.engine import run_orchestration_request
from orchestration.prompt_composer import PromptCompositionError


router = APIRouter(prefix="/api/v2/assistant", tags=["assistant-v2"])


@router.post("/chat", response_model=AssistantResponse)
def chat_v2(payload: AssistantRequest, authorization: str | None = Header(default=None)) -> AssistantResponse:
    cleanup_expired_sessions()
    user = decode_bearer_token(authorization)

    conversation_id = payload.conversationId or str(uuid.uuid4())
    session = get_or_create_session(conversation_id, user)

    if payload.role:
        session["role"] = payload.role
    if payload.userContext:
        session["user_context"] = payload.userContext
    if payload.sessionMetadata:
        session.setdefault("session_metadata", {}).update(payload.sessionMetadata)

    try:
        response_payload = run_orchestration_request(
            appcode=payload.appcode,
            message=payload.message,
            token=user.token,
            session=session,
            role=session.get("role"),
        )
    except (AppcodeResolutionError, DomainRoutingError, PromptCompositionError) as exc:
        return AssistantResponse(
            success=False,
            conversationId=conversation_id,
            appcode=(payload.appcode or "").strip().lower(),
            domain=session.get("resolved_domain") or "unknown",
            workflow=session.get("resolved_workflow"),
            error=str(exc),
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Unable to process orchestration request: {exc}") from exc

    return AssistantResponse(
        success=True,
        conversationId=conversation_id,
        appcode=session.get("appcode") or payload.appcode.strip().lower(),
        domain=session.get("resolved_domain") or "unknown",
        workflow=session.get("resolved_workflow"),
        response=response_payload,
    )


@router.delete("/chat/{conversation_id}")
def reset_chat_v2(conversation_id: str, authorization: str | None = Header(default=None)) -> dict[str, str]:
    """Reset a v2 conversation by ID for the authenticated caller."""
    decode_bearer_token(authorization)
    conversation_store.pop(conversation_id, None)
    return {"status": "cleared"}
