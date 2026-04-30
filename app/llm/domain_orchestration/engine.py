from __future__ import annotations

from llm.domain_orchestration.appcode_resolver import resolve_appcode
from llm.domain_orchestration.domain_executors import execute_domain_request
from llm.domain_orchestration.domain_router import resolve_domain_and_workflow
from llm.domain_orchestration.prompt_composer import compose_prompt


def run_orchestration_request(
    *,
    appcode: str,
    message: str,
    token: str,
    session: dict,
    role: str | None,
    registry: dict | None = None,
):
    """Resolve appcode/domain/workflow context, compose prompts, and execute the resolved domain runtime."""
    resolved_appcode, app_config = resolve_appcode(appcode, registry=registry)
    domain, workflow = resolve_domain_and_workflow(app_config, message)
    composed_prompt = compose_prompt(app_config, domain, workflow, role)

    session["appcode"] = resolved_appcode
    session["resolved_domain"] = domain
    session["resolved_workflow"] = workflow
    session["composed_prompt"] = composed_prompt
    session["available_workflows_by_domain"] = {
        domain_name: list((domain_config or {}).get("workflows", []))
        for domain_name, domain_config in (app_config.get("domains") or {}).items()
    }

    return execute_domain_request(app_config=app_config, domain=domain, message=message, token=token, session=session)
