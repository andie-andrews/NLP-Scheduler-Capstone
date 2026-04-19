import importlib
import importlib.util
import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

_LANGCHAIN_OPENAI_AVAILABLE = importlib.util.find_spec("langchain_openai") is not None
_LANGCHAIN_CORE_AVAILABLE = importlib.util.find_spec("langchain_core") is not None
LANGCHAIN_AVAILABLE = _LANGCHAIN_OPENAI_AVAILABLE and _LANGCHAIN_CORE_AVAILABLE

if LANGCHAIN_AVAILABLE:
    ChatOpenAI = importlib.import_module("langchain_openai").ChatOpenAI
    langchain_messages = importlib.import_module("langchain_core.messages")
    HumanMessage = langchain_messages.HumanMessage
    SystemMessage = langchain_messages.SystemMessage


@dataclass
class ModelResponse:
    """Unified response shape consumed by the existing orchestrator logic.

    Attributes:
        content: Assistant text content (empty when the model decides to only call tools).
        tool_calls: Tool call payload normalized to an OpenAI-like structure:
            [{"id": "...", "function": {"name": "...", "arguments": "{...json...}"}}]
    """

    content: str
    tool_calls: list[dict[str, Any]]


def _normalize_content(content: Any) -> str:
    """Convert provider-specific message content into a plain string.

    Why:
        LangChain/OpenAI can return content as either:
        - a direct string, or
        - a list of structured blocks.
        The orchestrator expects a single string, so we flatten and sanitize here.
    """

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        segments: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    segments.append(str(text))
            elif isinstance(item, str):
                segments.append(item)
        return "\n".join(segment.strip() for segment in segments if segment).strip()

    return ""


def _to_openai_tool_calls(tool_calls: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Normalize LangChain tool calls to the OpenAI tool-call shape.

    Why:
        The existing orchestrator parsing expects `function.name` and
        `function.arguments` (as JSON string). Keeping this shape avoids touching
        broad downstream business logic.
    """

    normalized = []
    for idx, tool_call in enumerate(tool_calls or [], start=1):
        normalized.append(
            {
                "id": tool_call.get("id") or f"lc_call_{idx}",
                "function": {
                    "name": tool_call.get("name"),
                    "arguments": json.dumps(tool_call.get("args") or {}),
                },
            }
        )
    return normalized


class OrchestrationLLM:
    """Small orchestration adapter that prefers LangChain but keeps OpenAI fallback.

    Why:
        - Centralizes model invocation in one place.
        - Reduces duplicated completion/tool-call code in `orchestrator.py`.
        - Allows teams to adopt LangChain incrementally without breaking existing flows.
    """

    def __init__(self, model: str = "gpt-4o", client: OpenAI | None = None):
        """Initialize the adapter.

        Args:
            model: Chat model name used by both LangChain and OpenAI fallback paths.
            client: Optional prebuilt OpenAI client (useful for tests/mocking).
        """

        self.model = model
        self._openai_client = client
        self._langchain_client = None

        if LANGCHAIN_AVAILABLE:
            # We intentionally create a single reusable ChatOpenAI client.
            # This keeps call-sites simple and avoids repeated client creation.
            self._langchain_client = ChatOpenAI(model=model, temperature=0)

    def _get_openai_client(self) -> OpenAI:
        """Lazily build the OpenAI client only when fallback is actually used.

        Why:
            Importing the orchestrator in tests/CLI should not require an API key
            unless a model call is made.
        """

        if self._openai_client is None:
            self._openai_client = OpenAI()
        return self._openai_client

    def invoke_with_tools(self, system_prompt: str, user_message: str, tools: list[dict[str, Any]]) -> ModelResponse:
        """Run a tool-aware chat turn and return a normalized response.

        Behavior:
            1) If LangChain is available, call `bind_tools(..., tool_choice="auto")`.
            2) Otherwise, fallback to OpenAI chat completions with the same tool schema.
        """

        if self._langchain_client:
            runnable = self._langchain_client.bind_tools(tools, tool_choice="auto")
            response = runnable.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message),
                ]
            )
            return ModelResponse(
                content=_normalize_content(response.content),
                tool_calls=_to_openai_tool_calls(getattr(response, "tool_calls", [])),
            )

        response = self._get_openai_client().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message
        tool_calls = []
        for tool_call in message.tool_calls or []:
            tool_calls.append(
                {
                    "id": tool_call.id,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
            )
        return ModelResponse(content=(message.content or "").strip(), tool_calls=tool_calls)

    def invoke_plain(self, system_prompt: str, user_message: str) -> str:
        """Run a plain conversational chat turn without tools.

        Why:
            The orchestrator uses this for non-scheduling/general conversation
            responses when no tool call is needed.
        """

        if self._langchain_client:
            response = self._langchain_client.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message),
                ]
            )
            return _normalize_content(response.content)

        response = self._get_openai_client().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return (response.choices[0].message.content or "").strip()
