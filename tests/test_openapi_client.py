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


def test_call_api_employee_query_filters_locally_and_avoids_non_empty_query():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)
    elif not hasattr(sys.modules["requests"], "get"):
        setattr(sys.modules["requests"], "get", lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    class _EmployeesResponse:
        status_code = 200
        text = '[{"id":1,"firstName":"John","lastName":"Doe"},{"id":5,"firstName":"Lori","lastName":"Martin"}]'

        def json(self):
            return [
                {"id": 1, "firstName": "John", "lastName": "Doe"},
                {"id": 5, "firstName": "Lori", "lastName": "Martin"},
            ]

    operation = {
        "method": "GET",
        "path": "/api/employees",
        "parameters": [{"name": "query", "in": "query", "schema": {"type": "string"}}],
        "requestBody": None,
    }

    with patch("app.llm.openapi_client.requests.get", return_value=_EmployeesResponse()) as mock_get:
        result = call_api("token", operation, {"query": "lori"})

    called_params = mock_get.call_args.kwargs["params"]
    assert called_params["query"] == ""
    assert result == [{"id": 5, "firstName": "Lori", "lastName": "Martin"}]
