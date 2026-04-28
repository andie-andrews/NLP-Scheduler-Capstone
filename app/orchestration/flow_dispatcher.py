from __future__ import annotations

from orchestration.flow_metadata import FLOW_METADATA


class FlowDispatchError(ValueError):
    """Raised when a flow dispatch is out of scope for app/domain policy."""


def dispatch_flow(
    appcode: str,
    app_config: dict,
    domain: str,
    workflow: str,
    handlers: dict,
    **kwargs,
):
    metadata = FLOW_METADATA.get(workflow)
    if metadata is None:
        raise FlowDispatchError(f"unknown workflow '{workflow}'")

    domain_config = (app_config.get("domains") or {}).get(domain)
    if not domain_config:
        raise FlowDispatchError(f"domain '{domain}' is not configured for appcode '{appcode}'")

    if workflow not in set(domain_config.get("workflows", [])):
        raise FlowDispatchError(f"workflow '{workflow}' is not available in domain '{domain}'")

    if metadata.get("domain") != domain:
        raise FlowDispatchError(f"workflow '{workflow}' does not belong to domain '{domain}'")

    primary = app_config.get("primary_domain")
    if domain != primary:
        allowed = set(((app_config.get("cross_domain") or {}).get(domain) or {}).get("allowed_workflows", []))
        if workflow not in allowed:
            raise FlowDispatchError(
                f"workflow '{workflow}' is not allowlisted for cross-domain route {primary} -> {domain}"
            )

    handler_name = metadata.get("handler")
    handler = handlers.get(handler_name)
    if handler is None:
        raise FlowDispatchError(f"handler '{handler_name}' is not registered")

    return handler(**kwargs)
