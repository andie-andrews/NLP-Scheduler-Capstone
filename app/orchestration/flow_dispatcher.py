from __future__ import annotations

from orchestration.flow_metadata import FlowMetadataError, build_workflow_domain_map, get_workflow_handler


class FlowDispatchError(ValueError):
    """Raised when a flow dispatch is out of scope for app/domain policy."""


def dispatch_flow(
    appcode: str,
    app_config: dict,
    domain: str,
    workflow: str,
    handlers: dict,
    registry: dict | None = None,
    **kwargs,
):
    """Dispatch a workflow after validating app/domain scope and cross-domain allowlists."""
    domain_config = (app_config.get("domains") or {}).get(domain)
    if not domain_config:
        raise FlowDispatchError(f"domain '{domain}' is not configured for appcode '{appcode}'")

    if workflow not in set(domain_config.get("workflows", [])):
        raise FlowDispatchError(f"workflow '{workflow}' is not available in domain '{domain}'")

    try:
        ownership = build_workflow_domain_map(registry=registry)
    except FlowMetadataError as exc:
        raise FlowDispatchError(str(exc)) from exc

    if ownership.get(workflow) != domain:
        raise FlowDispatchError(f"workflow '{workflow}' does not belong to domain '{domain}'")

    primary = app_config.get("primary_domain")
    if domain != primary:
        allowed = set(((app_config.get("cross_domain") or {}).get(domain) or {}).get("allowed_workflows", []))
        if workflow not in allowed:
            raise FlowDispatchError(
                f"workflow '{workflow}' is not allowlisted for cross-domain route {primary} -> {domain}"
            )

    try:
        handler_name = get_workflow_handler(workflow)
    except FlowMetadataError as exc:
        raise FlowDispatchError(str(exc)) from exc

    handler = handlers.get(handler_name)
    if handler is None:
        raise FlowDispatchError(f"handler '{handler_name}' is not registered")

    return handler(**kwargs)
