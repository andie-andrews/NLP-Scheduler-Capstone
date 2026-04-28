import pytest

from orchestration.domain_router import DomainRoutingError, resolve_domain_and_workflow


def test_employee_app_has_no_schedule_crossover():
    employee_app = {
        "primary_domain": "employee",
        "max_cross_domain_hops": 0,
        "cross_domain": {},
    }

    with pytest.raises(DomainRoutingError, match="not allowed"):
        resolve_domain_and_workflow(employee_app, "create shift for Alex")
