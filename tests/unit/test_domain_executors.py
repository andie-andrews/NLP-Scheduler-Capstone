import pytest

from orchestration.domain_executors import DomainExecutionError, execute_domain_request


def test_execute_domain_request_calls_registered_executor(monkeypatch):
    captured = {}

    def fake_executor(*, message: str, token: str, session: dict):
        captured["message"] = message
        captured["token"] = token
        captured["session"] = session
        return "ok"

    monkeypatch.setattr(
        "orchestration.domain_executors.DOMAIN_EXECUTORS",
        {"schedule": fake_executor, "employee": fake_executor},
    )

    result = execute_domain_request(domain="schedule", message="create shift", token="t", session={"id": 1})
    assert result == "ok"
    assert captured["message"] == "create shift"


def test_execute_domain_request_rejects_unknown_domain():
    with pytest.raises(DomainExecutionError, match="no configured executor"):
        execute_domain_request(domain="payroll", message="hello", token="t", session={})
