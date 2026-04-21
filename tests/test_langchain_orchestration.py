from types import SimpleNamespace

from app.llm.langchain_orchestration import OrchestrationLLM, _to_openai_tool_calls


class _FakeToolCall:
    def __init__(self, name: str, arguments: str):
        self.id = "call_1"
        self.function = SimpleNamespace(name=name, arguments=arguments)


class _FakeOpenAIClient:
    def __init__(self, message):
        self._message = message
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=self._message)])


def test_to_openai_tool_calls_converts_langchain_shape():
    normalized = _to_openai_tool_calls([
        {"id": "abc", "name": "getShifts", "args": {"employeeId": 7}},
    ])

    assert normalized == [
        {
            "id": "abc",
            "function": {
                "name": "getShifts",
                "arguments": '{"employeeId": 7}',
            },
        }
    ]


def test_invoke_with_tools_uses_openai_fallback_when_langchain_unavailable():
    message = SimpleNamespace(content="", tool_calls=[_FakeToolCall("getScheduleGroups", "{}")])
    client = _FakeOpenAIClient(message)

    llm = OrchestrationLLM(model="gpt-4o", client=client)
    llm._langchain_client = None

    response = llm.invoke_with_tools("system", "user", tools=[])

    assert response.tool_calls[0]["function"]["name"] == "getScheduleGroups"
    assert response.tool_calls[0]["function"]["arguments"] == "{}"


def test_invoke_plain_uses_openai_fallback_when_langchain_unavailable():
    message = SimpleNamespace(content="Hello from fallback", tool_calls=[])
    client = _FakeOpenAIClient(message)

    llm = OrchestrationLLM(model="gpt-4o", client=client)
    llm._langchain_client = None

    response = llm.invoke_plain("system", "user")

    assert response == "Hello from fallback"
