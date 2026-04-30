import pytest

from orchestration.domain_executors import DomainExecutionError, execute_domain_request


class FakePlugin:
    def execute(self, *, message: str, token: str, session: dict):
        return f"ok:{message}:{token}:{session.get('id')}"


def test_execute_domain_request_calls_registered_plugin(monkeypatch):
    monkeypatch.setattr(
        "orchestration.domain_executors.PLUGIN_REGISTRY",
        {"fake_plugin": FakePlugin()},
    )

    app_config = {
        "domains": {
            "schedule": {
                "plugin": "fake_plugin",
                "workflows": ["create_shift"],
            }
        }
    }

    result = execute_domain_request(
        app_config=app_config,
        domain="schedule",
        message="create shift",
        token="t",
        session={"id": 1},
    )
    assert result == "ok:create shift:t:1"


def test_execute_domain_request_rejects_unknown_domain():
    with pytest.raises(DomainExecutionError, match="no configured definition"):
        execute_domain_request(app_config={"domains": {}}, domain="payroll", message="hello", token="t", session={})


def test_execute_domain_request_rejects_unknown_plugin():
    app_config = {
        "domains": {
            "schedule": {
                "plugin": "missing_plugin",
                "workflows": ["create_shift"],
            }
        }
    }
    with pytest.raises(DomainExecutionError, match="is not registered"):
        execute_domain_request(app_config=app_config, domain="schedule", message="hello", token="t", session={})


def test_execute_domain_request_returns_pending_result_before_plugin(monkeypatch):
    monkeypatch.setattr(
        "orchestration.domain_executors.dispatch_pending_before_plugin",
        lambda **_: "pending-result",
    )

    called = {"plugin": False}

    class FailPlugin:
        def execute(self, **_kwargs):
            called["plugin"] = True
            return "plugin"

    monkeypatch.setattr(
        "orchestration.domain_executors.PLUGIN_REGISTRY",
        {"fake_plugin": FailPlugin()},
    )

    app_config = {
        "domains": {
            "schedule": {
                "plugin": "fake_plugin",
                "workflows": ["create_shift"],
            }
        }
    }

    result = execute_domain_request(
        app_config=app_config,
        domain="schedule",
        message="hello",
        token="t",
        session={},
    )
    assert result == "pending-result"
    assert called["plugin"] is False
