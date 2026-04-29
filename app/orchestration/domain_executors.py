from __future__ import annotations

from orchestration.domain_plugins import PLUGIN_REGISTRY


class DomainExecutionError(ValueError):
    """Raised when no runtime executor/plugin is configured for a resolved domain."""


def resolve_domain_plugin_name(app_config: dict, domain: str) -> str:
    """Resolve plugin name for a domain from app config, defaulting to legacy orchestrator plugin."""
    domain_config = (app_config.get("domains") or {}).get(domain) or {}
    return domain_config.get("plugin") or "schedule_orchestrator"


def execute_domain_request(*, app_config: dict, domain: str, message: str, token: str, session: dict):
    """Execute orchestration runtime for a resolved domain via configured domain plugin."""
    domain_config = (app_config.get("domains") or {}).get(domain)
    if not domain_config:
        raise DomainExecutionError(f"domain '{domain}' has no configured definition")

    plugin_name = resolve_domain_plugin_name(app_config, domain)
    plugin = PLUGIN_REGISTRY.get(plugin_name)
    if plugin is None:
        raise DomainExecutionError(f"plugin '{plugin_name}' is not registered for domain '{domain}'")

    return plugin.execute(message=message, token=token, session=session)
