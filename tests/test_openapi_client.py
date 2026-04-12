import importlib
import sys
import types
from unittest.mock import patch


class _DummyResponse:
    status_code = 200
    text = "{}"

    def json(self):
        return {}


def test_call_api_keeps_path_param_in_body_when_schema_requires_it():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(post=lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "method": "POST",
        "path": "/api/schedules/{scheduleId}/shifts",
        "parameters": [
            {"name": "scheduleId", "in": "path", "required": True, "schema": {"type": "integer"}},
        ],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "scheduleId": {"type": "integer"},
                            "employeeId": {"type": "integer"},
                        },
                    }
                }
            }
        },
    }

    with patch("app.llm.openapi_client.requests.post", return_value=_DummyResponse()) as mock_post:
        call_api("token", operation, {"scheduleId": 5, "employeeId": 1})

    body = mock_post.call_args.kwargs["json"]
    assert body["scheduleId"] == 5
    assert body["employeeId"] == 1


def test_call_api_removes_path_param_from_body_when_not_declared_in_schema():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(post=lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "method": "POST",
        "path": "/api/schedules/{scheduleId}/members",
        "parameters": [
            {"name": "scheduleId", "in": "path", "required": True, "schema": {"type": "integer"}},
        ],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "employeeId": {"type": "integer"},
                        },
                    }
                }
            }
        },
    }

    with patch("app.llm.openapi_client.requests.post", return_value=_DummyResponse()) as mock_post:
        call_api("token", operation, {"scheduleId": 5, "employeeId": 1})

    body = mock_post.call_args.kwargs["json"]
    assert "scheduleId" not in body
    assert body["employeeId"] == 1
