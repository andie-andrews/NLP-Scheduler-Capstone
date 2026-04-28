import pytest

from orchestration.flow_dispatcher import FlowDispatchError, dispatch_flow


SCHEDULING_APP = {
    "primary_domain": "schedule",
    "domains": {
        "schedule": {"workflows": ["create_shift"]},
        "employee": {"workflows": ["find_employee", "delete_employee"]},
    },
    "cross_domain": {
        "employee": {"allowed_workflows": ["find_employee"]},
    },
}


def test_dispatcher_blocks_out_of_scope_workflow():
    handlers = {"delete_employee": lambda **_: "ok"}
    with pytest.raises(FlowDispatchError, match="not allowlisted"):
        dispatch_flow(
            appcode="scheduling",
            app_config=SCHEDULING_APP,
            domain="employee",
            workflow="delete_employee",
            handlers=handlers,
        )


def test_dispatcher_calls_handler_for_allowed_workflow():
    handlers = {"create_shift": lambda **kwargs: f"created:{kwargs['employee_id']}"}
    result = dispatch_flow(
        appcode="scheduling",
        app_config=SCHEDULING_APP,
        domain="schedule",
        workflow="create_shift",
        handlers=handlers,
        employee_id=12,
    )
    assert result == "created:12"
