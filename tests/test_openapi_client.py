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


def test_call_api_uses_development_server_from_operation_spec():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)
    elif not hasattr(sys.modules["requests"], "get"):
        setattr(sys.modules["requests"], "get", lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "method": "GET",
        "path": "/api/employees",
        "servers": [
            {"url": "http://localhost/schedulerapi", "x-environment-name": "development"},
            {"url": "https://prod.example.com", "x-environment-name": "production"},
        ],
        "parameters": [],
        "requestBody": None,
    }

    with (
        patch.dict("os.environ", {"ASPNETCORE_ENVIRONMENT": "Development"}),
        patch("app.llm.openapi_client.requests.get", return_value=_DummyResponse()) as mock_get,
    ):
        call_api("token", operation, {})

    called_url = mock_get.call_args.args[0]
    assert called_url == "http://localhost/schedulerapi/api/employees"


def test_call_api_defaults_to_local_iis_url_in_non_production_env():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)
    elif not hasattr(sys.modules["requests"], "get"):
        setattr(sys.modules["requests"], "get", lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "method": "GET",
        "path": "/api/employees",
        "parameters": [],
        "requestBody": None,
    }

    with (
        patch.dict("os.environ", {"ASPNETCORE_ENVIRONMENT": "Development"}, clear=True),
        patch("app.llm.openapi_client.requests.get", return_value=_DummyResponse()) as mock_get,
    ):
        call_api("token", operation, {})

    called_url = mock_get.call_args.args[0]
    assert called_url == "http://localhost/schedulerapi/api/employees"


def test_call_api_defaults_to_production_url_in_production_env():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)
    elif not hasattr(sys.modules["requests"], "get"):
        setattr(sys.modules["requests"], "get", lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "method": "GET",
        "path": "/api/employees",
        "servers": [
            {"url": "http://localhost/schedulerapi", "x-environment-name": "development"},
            {"url": "https://prod.example.com", "x-environment-name": "production"},
        ],
        "parameters": [],
        "requestBody": None,
    }

    with (
        patch.dict("os.environ", {"ASPNETCORE_ENVIRONMENT": "Production"}, clear=True),
        patch("app.llm.openapi_client.requests.get", return_value=_DummyResponse()) as mock_get,
    ):
        call_api("token", operation, {})

    called_url = mock_get.call_args.args[0]
    assert called_url == "https://prod.example.com/api/employees"


def test_call_api_uses_scheduler_runtime_env_to_select_server():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)
    elif not hasattr(sys.modules["requests"], "get"):
        setattr(sys.modules["requests"], "get", lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "method": "GET",
        "path": "/api/employees",
        "servers": [
            {"url": "http://localhost/schedulerapi", "x-environment-name": "development"},
            {"url": "https://prod.example.com", "x-environment-name": "production"},
        ],
        "parameters": [],
        "requestBody": None,
    }

    with (
        patch.dict("os.environ", {"SCHEDULER_RUNTIME_ENV": "production"}, clear=True),
        patch("app.llm.openapi_client.requests.get", return_value=_DummyResponse()) as mock_get,
    ):
        call_api("token", operation, {})

    called_url = mock_get.call_args.args[0]
    assert called_url == "https://prod.example.com/api/employees"


def test_call_api_prefers_explicit_base_url_override():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)
    elif not hasattr(sys.modules["requests"], "get"):
        setattr(sys.modules["requests"], "get", lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "method": "GET",
        "path": "/api/employees",
        "servers": [
            {"url": "http://localhost/schedulerapi", "x-environment-name": "development"},
            {"url": "https://prod.example.com", "x-environment-name": "production"},
        ],
        "parameters": [],
        "requestBody": None,
    }

    with (
        patch.dict(
            "os.environ",
            {
                "SCHEDULER_RUNTIME_ENV": "production",
                "SCHEDULER_API_BASE_URL": "https://staging.example.com/custom-base/",
            },
            clear=True,
        ),
        patch("app.llm.openapi_client.requests.get", return_value=_DummyResponse()) as mock_get,
    ):
        call_api("token", operation, {})

    called_url = mock_get.call_args.args[0]
    assert called_url == "https://staging.example.com/custom-base/api/employees"


def test_call_api_prefers_api_specific_base_url_override():
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)
    elif not hasattr(sys.modules["requests"], "get"):
        setattr(sys.modules["requests"], "get", lambda *args, **kwargs: None)
    call_api = importlib.import_module("app.llm.openapi_client").call_api

    operation = {
        "api_name": "employee",
        "method": "GET",
        "path": "/api/employees",
        "servers": [
            {"url": "http://localhost/employeeapi", "x-environment-name": "development"},
            {"url": "https://prod.employee.example.com", "x-environment-name": "production"},
        ],
        "parameters": [],
        "requestBody": None,
    }

    with (
        patch.dict(
            "os.environ",
            {
                "SCHEDULER_RUNTIME_ENV": "production",
                "EMPLOYEE_API_BASE_URL": "https://employee.staging.example.com/base/",
            },
            clear=True,
        ),
        patch("app.llm.openapi_client.requests.get", return_value=_DummyResponse()) as mock_get,
    ):
        call_api("token", operation, {})

    called_url = mock_get.call_args.args[0]
    assert called_url == "https://employee.staging.example.com/base/api/employees"
