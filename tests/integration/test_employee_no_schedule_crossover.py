import pytest

from orchestration.domain_router import DomainRoutingError, resolve_domain_and_workflow


def test_employee_app_has_no_schedule_crossover():
    employee_app = {
        "primary_domain": "employee",
        "max_cross_domain_hops": 0,
        "domains": {"employee": {"workflows": ["find_employee", "create_employee", "update_employee", "delete_employee"]}},
        "cross_domain": {},
    }

    with pytest.raises(DomainRoutingError, match="not configured"):
        resolve_domain_and_workflow(employee_app, "create shift for Alex")


def test_employee_app_fails_closed_for_unmapped_schedule_like_prompts():
    employee_app = {
        "primary_domain": "employee",
        "max_cross_domain_hops": 0,
        "domains": {"employee": {"workflows": ["find_employee", "create_employee", "update_employee", "delete_employee"]}},
        "cross_domain": {},
    }

    with pytest.raises(DomainRoutingError, match="unable to map request intent"):
        resolve_domain_and_workflow(employee_app, "show my shifts this week")
