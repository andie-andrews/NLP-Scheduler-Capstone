from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    """V2 assistant request contract with required appcode routing context."""

    appcode: str = Field(min_length=1)
    message: str = Field(min_length=1)
    conversationId: str | None = None
    sessionMetadata: dict[str, Any] | None = None


class AssistantResponse(BaseModel):
    """V2 assistant response contract with structured success/error fields."""

    success: bool
    conversationId: str
    appcode: str
    domain: str
    workflow: str | None = None
    response: Any | None = None
    error: str | None = None
