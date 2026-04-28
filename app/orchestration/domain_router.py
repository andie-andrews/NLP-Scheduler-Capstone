from __future__ import annotations

from llm.orchestration.intents import (
    is_add_schedule_member_intent,
    is_create_employee_intent,
    is_create_schedule_intent,
    is_create_shift_intent,
    is_delete_employee_intent,
    is_delete_schedule_intent,
    is_delete_shift_intent,
    is_get_manager_schedule_groups_intent,
    is_remove_schedule_member_intent,
    is_update_employee_intent,
    is_update_shift_intent,
)


class DomainRoutingError(ValueError):
    """Raised when cross-domain or domain policy is violated."""


FLOW_TO_DOMAIN = {
    "create_shift": "schedule",
    "update_shift": "schedule",
    "delete_shift": "schedule",
    "create_schedule": "schedule",
    "add_schedule_member": "schedule",
    "remove_schedule_member": "schedule",
    "delete_schedule": "schedule",
    "get_manager_schedule_groups": "schedule",
    "find_employee": "employee",
    "create_employee": "employee",
    "update_employee": "employee",
    "delete_employee": "employee",
}


def infer_workflow_from_message(message: str) -> str | None:
    if is_create_shift_intent(message):
        return "create_shift"
    if is_update_shift_intent(message):
        return "update_shift"
    if is_delete_shift_intent(message):
        return "delete_shift"
    if is_create_schedule_intent(message):
        return "create_schedule"
    if is_add_schedule_member_intent(message):
        return "add_schedule_member"
    if is_remove_schedule_member_intent(message):
        return "remove_schedule_member"
    if is_delete_schedule_intent(message):
        return "delete_schedule"
    if is_get_manager_schedule_groups_intent(message):
        return "get_manager_schedule_groups"
    if is_create_employee_intent(message):
        return "create_employee"
    if is_update_employee_intent(message):
        return "update_employee"
    if is_delete_employee_intent(message):
        return "delete_employee"
    return None


def resolve_domain_and_workflow(app_config: dict, message: str, max_hops: int | None = None) -> tuple[str, str | None]:
    primary_domain = app_config.get("primary_domain")
    workflow = infer_workflow_from_message(message)
    if workflow is None:
        return primary_domain, None

    target_domain = FLOW_TO_DOMAIN.get(workflow)
    if target_domain == primary_domain:
        return target_domain, workflow

    cross_domain = app_config.get("cross_domain", {})
    if target_domain not in cross_domain:
        raise DomainRoutingError(f"cross-domain route from {primary_domain} to {target_domain} is not allowed")

    if (max_hops if max_hops is not None else app_config.get("max_cross_domain_hops", 0)) < 1:
        raise DomainRoutingError(f"cross-domain route from {primary_domain} to {target_domain} exceeds hop limit")

    allowlisted = set(cross_domain.get(target_domain, {}).get("allowed_workflows", []))
    if workflow not in allowlisted:
        raise DomainRoutingError(f"workflow '{workflow}' is not allowlisted for {primary_domain} -> {target_domain}")

    return target_domain, workflow
