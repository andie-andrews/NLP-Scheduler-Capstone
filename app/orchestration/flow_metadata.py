from __future__ import annotations

from orchestration.appcode_resolver import load_app_registry, load_registry_payload


class FlowMetadataError(ValueError):
    """Raised when workflow metadata cannot be derived from the app registry."""


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


def get_workflow_handler(workflow: str, registry_payload: dict | None = None) -> str:
    """Resolve canonical handler key for a workflow from app registry configuration."""
    payload = registry_payload or load_registry_payload()
    handler_map = payload.get("workflow_handlers") or {}
    handler = handler_map.get(workflow)
    if not handler:
        raise FlowMetadataError(f"workflow '{workflow}' is missing a handler mapping in app_registry.json")
    return handler
