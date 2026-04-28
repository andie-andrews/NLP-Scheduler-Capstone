from __future__ import annotations

from orchestration.appcode_resolver import load_app_registry


class FlowMetadataError(ValueError):
    """Raised when workflow metadata cannot be derived from the app registry."""


FLOW_HANDLER_MAP: dict[str, str] = {
    "create_shift": "create_shift",
    "update_shift": "update_shift",
    "delete_shift": "delete_shift",
    "create_schedule": "create_schedule",
    "add_schedule_member": "add_schedule_member",
    "remove_schedule_member": "remove_schedule_member",
    "delete_schedule": "delete_schedule",
    "get_manager_schedule_groups": "get_manager_schedule_groups",
    "find_employee": "find_employee",
    "create_employee": "create_employee",
    "update_employee": "update_employee",
    "delete_employee": "delete_employee",
}


def build_workflow_domain_map(registry: dict | None = None) -> dict[str, str]:
    """Build canonical workflow->domain ownership from app registry domain workflow lists."""
    apps = registry or load_app_registry()
    ownership: dict[str, str] = {}

    for app_config in apps.values():
        for domain, domain_config in (app_config.get("domains") or {}).items():
            for workflow in domain_config.get("workflows", []):
                current_owner = ownership.get(workflow)
                if current_owner and current_owner != domain:
                    raise FlowMetadataError(
                        f"workflow '{workflow}' is assigned to multiple domains: {current_owner}, {domain}"
                    )
                ownership[workflow] = domain

    return ownership


def get_workflow_handler(workflow: str) -> str:
    """Resolve canonical handler key for a workflow."""
    handler = FLOW_HANDLER_MAP.get(workflow)
    if not handler:
        raise FlowMetadataError(f"workflow '{workflow}' is missing a handler mapping")
    return handler
