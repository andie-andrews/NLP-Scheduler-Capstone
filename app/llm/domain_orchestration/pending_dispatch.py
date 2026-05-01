from __future__ import annotations

from llm.orchestration.state_store import (
    get_pending_employee_operation_state,
    has_any_pending_state,
)

WORKFLOW_PENDING_KEYS = {
    "create_shift": "pending_create_shift",
    "update_shift": "pending_update_shift",
    "delete_shift": "pending_delete_shift",
    "create_schedule": "pending_create_schedule",
    "add_schedule_member": "pending_schedule_member_change",
    "remove_schedule_member": "pending_schedule_member_change",
    "delete_schedule": "pending_delete_schedule",
}

SCHEDULE_AUX_PENDING_KEYS = ["pending_show_shifts", "pending_employee_operation"]


def dispatch_pending_before_plugin(
    *,
    domain: str,
    plugin_name: str,
    configured_workflows: list[str],
    message: str,
    token: str,
    session: dict,
):
    """Dispatch domain-specific pending workflows before plugin runtime execution."""
    if domain == "schedule":
        pending_keys = {
            WORKFLOW_PENDING_KEYS[workflow]
            for workflow in configured_workflows or []
            if workflow in WORKFLOW_PENDING_KEYS
        }
        pending_keys.update(SCHEDULE_AUX_PENDING_KEYS)
        has_pending_schedule_state = has_any_pending_state(session, list(pending_keys))
        if not has_pending_schedule_state:
            return None

        # Reuse configured scheduling plugin dispatch instead of hardcoding
        # a specific module import to keep this dispatcher domain-driven.
        from llm.domain_orchestration.domain_plugins import PLUGIN_REGISTRY

        plugin = PLUGIN_REGISTRY.get(plugin_name)
        if plugin is None:
            return None
        return plugin.execute(message=message, token=token, session=session)

    if domain == "employee":
        if not has_any_pending_state(session, ["pending_employee_operation"]):
            return None

        from llm.domain_orchestration.domains.employee.plugins.employee_orchestrator import run_employee_orchestrator

        return run_employee_orchestrator(message=message, token=token, session=session)

    return None
