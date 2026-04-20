from llm.openapi_parser import parse_operations, parse_operations_by_api
from llm.orchestration.tools import build_tools


def test_parse_operations_by_api_keeps_duplicate_operation_ids_distinct():
    specs_by_api = {
        "hr": {
            "paths": {
                "/employees": {
                    "post": {
                        "operationId": "createEntity",
                        "summary": "Create employee",
                        "parameters": [{"name": "tenantId", "in": "query", "schema": {"type": "string"}}],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                        "required": ["name"],
                                    }
                                }
                            }
                        },
                    }
                }
            }
        },
        "payroll": {
            "paths": {
                "/payees": {
                    "post": {
                        "operationId": "createEntity",
                        "summary": "Create payee",
                        "parameters": [{"name": "region", "in": "query", "schema": {"type": "string"}}],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"legalName": {"type": "string"}},
                                        "required": ["legalName"],
                                    }
                                }
                            }
                        },
                    }
                }
            }
        },
    }

    operations = parse_operations_by_api(specs_by_api)

    assert "hr__createEntity" in operations
    assert "payroll__createEntity" in operations

    hr_op = operations["hr__createEntity"]
    payroll_op = operations["payroll__createEntity"]

    assert hr_op["api_name"] == "hr"
    assert payroll_op["api_name"] == "payroll"
    assert hr_op["operationId"] == "createEntity"
    assert payroll_op["operationId"] == "createEntity"
    assert hr_op["method"] == "POST"
    assert payroll_op["method"] == "POST"
    assert hr_op["path"] == "/employees"
    assert payroll_op["path"] == "/payees"
    assert hr_op["parameters"][0]["name"] == "tenantId"
    assert payroll_op["parameters"][0]["name"] == "region"
    assert hr_op["requestBody"] is not None
    assert payroll_op["requestBody"] is not None


def test_build_tools_uses_namespaced_callable_name_for_function_name():
    operations = {
        "hr__createEntity": {
            "api_name": "hr",
            "operationId": "createEntity",
            "callable_id": "hr__createEntity",
            "method": "POST",
            "path": "/employees",
            "parameters": [],
            "requestBody": None,
            "summary": "Create employee",
        },
        "payroll__createEntity": {
            "api_name": "payroll",
            "operationId": "createEntity",
            "callable_id": "payroll__createEntity",
            "method": "POST",
            "path": "/payees",
            "parameters": [],
            "requestBody": None,
            "summary": "Create payee",
        },
    }

    tools = build_tools(operations)
    function_names = [tool["function"]["name"] for tool in tools]

    assert "hr__createEntity" in function_names
    assert "payroll__createEntity" in function_names


def test_parse_operations_keeps_operation_id_keys_for_single_spec():
    spec = {
        "paths": {
            "/employees/{employeeId}": {
                "get": {
                    "operationId": "getEmployee",
                    "parameters": [],
                }
            }
        }
    }

    operations = parse_operations(spec)

    assert "getEmployee" in operations
    assert operations["getEmployee"]["api_name"] == "default"
    assert operations["getEmployee"]["operationId"] == "getEmployee"
    assert operations["getEmployee"]["callable_id"] == "default__getEmployee"
