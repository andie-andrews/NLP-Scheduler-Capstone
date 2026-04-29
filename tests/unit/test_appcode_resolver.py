import pytest

from orchestration.appcode_resolver import AppcodeResolutionError, resolve_appcode


REGISTRY = {
    "scheduling": {"primary_domain": "schedule"},
    "employee": {"primary_domain": "employee"},
}


def test_appcode_required_and_validated():
    with pytest.raises(AppcodeResolutionError, match="appcode is required"):
        resolve_appcode("", registry=REGISTRY)


def test_unknown_appcode_rejected():
    with pytest.raises(AppcodeResolutionError, match="unknown appcode"):
        resolve_appcode("payroll", registry=REGISTRY)


def test_known_appcode_resolves():
    appcode, config = resolve_appcode("Scheduling", registry=REGISTRY)
    assert appcode == "scheduling"
    assert config["primary_domain"] == "schedule"
