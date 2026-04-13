from app.llm.orchestration.resolvers import resolve_employee_id


def _ops():
    return {"searchEmployees": {"method": "GET", "path": "/api/employees", "parameters": []}}


def test_resolve_employee_id_uses_directory_search_with_empty_query():
    calls = []

    def fake_api_caller(_token, _op, args):
        calls.append(args)
        return [
            {"id": 1, "firstName": "John", "lastName": "Doe"},
            {"id": 5, "firstName": "Lori", "lastName": "Martin"},
        ]

    result = resolve_employee_id("token", "lori", _ops(), fake_api_caller)

    assert result == {"type": "resolved", "employeeId": 5}
    assert calls == [{"query": ""}]


def test_resolve_employee_id_disambiguates_multiple_first_name_matches():
    def fake_api_caller(_token, _op, _args):
        return [
            {"id": 1, "firstName": "John", "lastName": "Doe"},
            {"id": 2, "firstName": "John", "lastName": "Smith"},
        ]

    result = resolve_employee_id("token", "john", _ops(), fake_api_caller)

    assert result["type"] == "disambiguation"
    assert len(result["raw"]) == 2
