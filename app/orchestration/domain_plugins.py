from __future__ import annotations

from typing import Protocol


class DomainPlugin(Protocol):
    """Contract for pluggable domain runtime execution."""

    def execute(self, *, message: str, token: str, session: dict):
        """Execute a domain request using plugin-specific runtime logic."""


class LegacyOrchestratorPlugin:
    """Plugin adapter that routes execution to the existing legacy orchestrator runtime."""

    def execute(self, *, message: str, token: str, session: dict):
        from llm.orchestrator import run_orchestrator

        return run_orchestrator(message=message, token=token, session=session)


PLUGIN_REGISTRY: dict[str, DomainPlugin] = {
    "legacy_orchestrator": LegacyOrchestratorPlugin(),
}
