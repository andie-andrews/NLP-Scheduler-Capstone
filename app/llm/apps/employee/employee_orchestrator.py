from __future__ import annotations

from llm.apps.scheduling.schedule_orchestrator import run_orchestrator as run_schedule_orchestrator


def run_employee_orchestrator(message: str, token: str, session: dict):
    """Employee-domain orchestrator entrypoint.

    Current runtime reuses shared orchestration behavior while exposing an employee
    appcode/domain-specific module boundary for incremental divergence.
    """
    session["orchestrator_domain"] = "employee"
    return run_schedule_orchestrator(message=message, token=token, session=session)
