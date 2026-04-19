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
    content: str
    tool_calls: list[dict[str, Any]]


def _normalize_content(content: Any) -> str:
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
    def __init__(self, model: str = "gpt-4o", client: OpenAI | None = None):
        self.model = model
        self._openai_client = client
        self._langchain_client = None

        if LANGCHAIN_AVAILABLE:
            self._langchain_client = ChatOpenAI(model=model, temperature=0)

    def _get_openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI()
        return self._openai_client

    def invoke_with_tools(self, system_prompt: str, user_message: str, tools: list[dict[str, Any]]) -> ModelResponse:
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
