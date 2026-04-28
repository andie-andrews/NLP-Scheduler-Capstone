from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    appcode: str = Field(min_length=1)
    message: str = Field(min_length=1)
    conversationId: str | None = None
    role: str | None = None
    userContext: dict[str, Any] | None = None
    sessionMetadata: dict[str, Any] | None = None


class AssistantResponse(BaseModel):
    success: bool
    conversationId: str
    appcode: str
    domain: str
    workflow: str | None = None
    response: Any | None = None
    error: str | None = None
