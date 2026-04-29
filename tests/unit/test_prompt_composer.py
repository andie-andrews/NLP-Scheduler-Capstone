import pytest

from orchestration.prompt_composer import PromptCompositionError, compose_prompt


def test_prompt_composition_order_is_correct():
    app_config = {
        "prompts": {
            "global": "GLOBAL",
            "appcode": "APPCODE",
            "domains": {"schedule": "DOMAIN"},
            "flows": {"create_shift": "FLOW"},
            "roles": {"Supervisor": "ROLE"},
        }
    }

    composed = compose_prompt(app_config, "schedule", "create_shift", "Supervisor")
    assert composed == "GLOBAL\n\nAPPCODE\n\nDOMAIN\n\nFLOW\n\nROLE"


def test_prompt_composer_errors_on_missing_required_segments():
    with pytest.raises(PromptCompositionError, match="missing prompts.global"):
        compose_prompt({"prompts": {}}, "schedule", None, None)
