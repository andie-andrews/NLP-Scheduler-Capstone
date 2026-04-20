import os

from llm.openapi_parser import parse_operations

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from llm.orchestrator import _resolve_operation_for_tool_call


def test_resolve_operation_for_namespaced_tool_name():
    spec = {
        "paths": {
            "/employees/{employeeId}/shifts": {
                "get": {
                    "operationId": "getEmployeeShifts",
                    "parameters": [],
                }
            }
        }
    }
    operations = parse_operations(spec)

    op_key, op_id = _resolve_operation_for_tool_call("default__getEmployeeShifts", operations)

    assert op_key == "getEmployeeShifts"
    assert op_id == "getEmployeeShifts"


def test_resolve_operation_for_non_namespaced_tool_name():
    spec = {
        "paths": {
            "/employees/{employeeId}/shifts": {
                "get": {
                    "operationId": "getEmployeeShifts",
                    "parameters": [],
                }
            }
        }
    }
    operations = parse_operations(spec)

    op_key, op_id = _resolve_operation_for_tool_call("getEmployeeShifts", operations)

    assert op_key == "getEmployeeShifts"
    assert op_id == "getEmployeeShifts"
