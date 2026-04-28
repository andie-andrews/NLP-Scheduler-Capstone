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


def infer_workflow_from_message(message: str) -> str | None:
    """Infer workflow key from the incoming user message using existing intent matchers."""
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


def _flow_to_domain_map_for_app(app_config: dict) -> dict[str, str]:
    """Build workflow->domain ownership for the resolved app from app registry domain workflow definitions."""
    ownership: dict[str, str] = {}
    for domain, domain_config in (app_config.get("domains") or {}).items():
        for workflow in domain_config.get("workflows", []):
            current_owner = ownership.get(workflow)
            if current_owner and current_owner != domain:
                raise DomainRoutingError(
                    f"workflow '{workflow}' is assigned to multiple domains: {current_owner}, {domain}"
                )
            ownership[workflow] = domain
    return ownership


def resolve_domain_and_workflow(app_config: dict, message: str, max_hops: int | None = None) -> tuple[str, str | None]:
    """Resolve request domain/workflow while enforcing directional cross-domain policy rules."""
    primary_domain = app_config.get("primary_domain")
    workflow = infer_workflow_from_message(message)
    if workflow is None:
        return primary_domain, None

    flow_to_domain = _flow_to_domain_map_for_app(app_config)
    target_domain = flow_to_domain.get(workflow)
    if target_domain is None:
        raise DomainRoutingError(f"workflow '{workflow}' is not configured for this app")

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
