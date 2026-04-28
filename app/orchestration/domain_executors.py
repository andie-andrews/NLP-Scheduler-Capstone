from __future__ import annotations

from orchestration.domains.employee_executor import execute_employee_domain
from orchestration.domains.schedule_executor import execute_schedule_domain


class DomainExecutionError(ValueError):
    """Raised when no runtime executor is configured for a resolved domain."""


DOMAIN_EXECUTORS = {
    "schedule": execute_schedule_domain,
    "employee": execute_employee_domain,
}


def execute_domain_request(*, domain: str, message: str, token: str, session: dict):
    """Execute orchestration runtime for a resolved domain via centralized executors."""
    executor = DOMAIN_EXECUTORS.get(domain)
    if executor is None:
        raise DomainExecutionError(f"domain '{domain}' has no configured executor")
    return executor(message=message, token=token, session=session)
