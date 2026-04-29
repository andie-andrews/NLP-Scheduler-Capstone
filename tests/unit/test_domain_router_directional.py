import pytest

from orchestration.domain_router import DomainRoutingError, resolve_domain_and_workflow


SCHEDULING_APP = {
    "primary_domain": "schedule",
    "max_cross_domain_hops": 1,
    "domains": {
        "schedule": {"workflows": ["create_shift", "update_shift", "delete_shift", "create_schedule", "add_schedule_member", "remove_schedule_member", "delete_schedule", "get_manager_schedule_groups"]},
        "employee": {"workflows": ["find_employee", "create_employee", "update_employee", "delete_employee"]},
    },
    "cross_domain": {
        "employee": {
            "allowed_workflows": ["find_employee", "create_employee", "update_employee"],
        }
    },
}

EMPLOYEE_APP = {
    "primary_domain": "employee",
    "max_cross_domain_hops": 0,
    "domains": {
        "employee": {"workflows": ["find_employee", "create_employee", "update_employee", "delete_employee"]},
    },
    "cross_domain": {},
}


def test_scheduling_routes_schedule_intents_normally():
    domain, workflow = resolve_domain_and_workflow(SCHEDULING_APP, "create shift for Jane tomorrow")
    assert domain == "schedule"
    assert workflow == "create_shift"


def test_scheduling_can_use_allowlisted_employee_cross_domain_workflows():
    domain, workflow = resolve_domain_and_workflow(SCHEDULING_APP, "create employee Jane Doe")
    assert domain == "employee"
    assert workflow == "create_employee"


def test_scheduling_blocks_disallowed_employee_cross_domain_workflow():
    with pytest.raises(DomainRoutingError, match="not allowlisted"):
        resolve_domain_and_workflow(SCHEDULING_APP, "delete employee Jane Doe")


def test_employee_app_cannot_route_to_schedule_workflows():
    with pytest.raises(DomainRoutingError, match="not configured"):
        resolve_domain_and_workflow(EMPLOYEE_APP, "create shift for Jane")
