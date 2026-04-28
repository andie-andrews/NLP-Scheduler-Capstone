from __future__ import annotations


def execute_schedule_domain(*, message: str, token: str, session: dict):
    """Run schedule-domain orchestration through the existing legacy schedule orchestrator."""
    from llm.orchestrator import run_orchestrator

    return run_orchestrator(message=message, token=token, session=session)
