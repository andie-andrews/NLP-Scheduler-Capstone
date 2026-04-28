from __future__ import annotations


def execute_employee_domain(*, message: str, token: str, session: dict):
    """Run employee-domain orchestration through the current orchestrator runtime."""
    from llm.orchestrator import run_orchestrator

    return run_orchestrator(message=message, token=token, session=session)
