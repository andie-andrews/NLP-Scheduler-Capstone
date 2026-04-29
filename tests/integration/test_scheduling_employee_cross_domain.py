import pytest

from orchestration.domain_router import resolve_domain_and_workflow
from orchestration.flow_dispatcher import FlowDispatchError, dispatch_flow


def test_scheduling_employee_cross_domain_allowlist_enforced():
    app_config = {
        "primary_domain": "schedule",
        "max_cross_domain_hops": 1,
        "domains": {
            "schedule": {"workflows": ["create_shift"]},
            "employee": {"workflows": ["find_employee", "create_employee", "update_employee", "delete_employee"]},
        },
        "cross_domain": {"employee": {"allowed_workflows": ["find_employee", "create_employee", "update_employee"]}},
    }

    domain, workflow = resolve_domain_and_workflow(app_config, "create employee Alex")
    assert (domain, workflow) == ("employee", "create_employee")

    with pytest.raises(FlowDispatchError, match="not allowlisted"):
        dispatch_flow(
            appcode="scheduling",
            app_config=app_config,
            domain="employee",
            workflow="delete_employee",
            handlers={"delete_employee": lambda **_: "never"},
        )
