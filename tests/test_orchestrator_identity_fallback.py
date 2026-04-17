import jwt

from llm.orchestrator import _extract_employee_id_from_token


def test_extract_employee_id_from_token_reads_employee_id_claim():
    token = jwt.encode({"employeeId": "42"}, key="x" * 32, algorithm="HS256")

    assert _extract_employee_id_from_token(token) == 42


def test_extract_employee_id_from_token_returns_none_for_invalid_or_missing_claim():
    missing_claim_token = jwt.encode({"role": "Supervisor"}, key="x" * 32, algorithm="HS256")

    assert _extract_employee_id_from_token(missing_claim_token) is None
    assert _extract_employee_id_from_token("not-a-token") is None
