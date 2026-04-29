from __future__ import annotations

from orchestration.appcode_resolver import resolve_appcode
from orchestration.domain_executors import execute_domain_request
from orchestration.domain_router import resolve_domain_and_workflow
from orchestration.prompt_composer import compose_prompt


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

    return execute_domain_request(domain=domain, message=message, token=token, session=session)
