from __future__ import annotations


class PromptCompositionError(ValueError):
    """Raised when required prompt segment cannot be found."""


def compose_prompt(app_config: dict, domain: str, workflow: str | None, role: str | None) -> str:
    prompts = app_config.get("prompts") or {}
    segments: list[str] = []

    global_segment = prompts.get("global")
    appcode_segment = prompts.get("appcode")
    domain_segment = (prompts.get("domains") or {}).get(domain)
    role_segment = (prompts.get("roles") or {}).get(role) if role else None

    if not global_segment:
        raise PromptCompositionError("missing prompts.global")
    if not appcode_segment:
        raise PromptCompositionError("missing prompts.appcode")
    if not domain_segment:
        raise PromptCompositionError(f"missing domain prompt for '{domain}'")

    segments.extend([global_segment, appcode_segment, domain_segment])

    if workflow:
        flow_segment = (prompts.get("flows") or {}).get(workflow)
        if not flow_segment:
            raise PromptCompositionError(f"missing flow prompt for '{workflow}'")
        segments.append(flow_segment)

    if role and not role_segment:
        raise PromptCompositionError(f"missing role prompt for '{role}'")
    if role_segment:
        segments.append(role_segment)

    return "\n\n".join(segments)
