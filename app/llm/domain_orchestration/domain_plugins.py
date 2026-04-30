from __future__ import annotations

from typing import Protocol


class DomainPlugin(Protocol):
    """Contract for pluggable domain runtime execution."""

    def execute(self, *, message: str, token: str, session: dict):
        """Execute a domain request using plugin-specific runtime logic."""


class ScheduleOrchestratorPlugin:
    """Plugin adapter that routes schedule execution to schedule orchestrator runtime."""

    def execute(self, *, message: str, token: str, session: dict):
        from llm.domain_orchestration.domains.scheduling.plugins.schedule_orchestrator import run_orchestrator

        return run_orchestrator(message=message, token=token, session=session)


class EmployeeOrchestratorPlugin:
    """Plugin adapter that routes employee execution to employee orchestrator runtime."""

    def execute(self, *, message: str, token: str, session: dict):
        from llm.domain_orchestration.domains.employee.plugins.employee_orchestrator import run_employee_orchestrator

        return run_employee_orchestrator(message=message, token=token, session=session)


PLUGIN_REGISTRY: dict[str, DomainPlugin] = {
    "schedule_orchestrator": ScheduleOrchestratorPlugin(),
    "employee_orchestrator": EmployeeOrchestratorPlugin(),
}
