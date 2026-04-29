from __future__ import annotations


class DomainExecutionError(ValueError):
    """Raised when no runtime executor is configured for a resolved domain."""


def execute_legacy_orchestrator_domain(*, message: str, token: str, session: dict):
    """Execute a domain through the current shared legacy orchestrator runtime.

    Both `schedule` and `employee` currently run through the same orchestrator
    implementation. Domain-specific executors can be split out later when
    domain runtimes diverge.
    """
    from llm.orchestrator import run_orchestrator

    return run_orchestrator(message=message, token=token, session=session)


DOMAIN_EXECUTORS = {
    "schedule": execute_legacy_orchestrator_domain,
    "employee": execute_legacy_orchestrator_domain,
}


def execute_domain_request(*, domain: str, message: str, token: str, session: dict):
    """Execute orchestration runtime for a resolved domain via centralized executors."""
    executor = DOMAIN_EXECUTORS.get(domain)
    if executor is None:
        raise DomainExecutionError(f"domain '{domain}' has no configured executor")
    return executor(message=message, token=token, session=session)
