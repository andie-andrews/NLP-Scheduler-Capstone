import os
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")
from llm import orchestrator


def test_run_orchestrator_creates_schedule_group_from_manager_group_message():
    operations = {"createScheduleGroup": "create-schedule-op"}

    def fake_call_api(_token, operation, args):
        if operation == "create-schedule-op":
            assert args == {"name": "Kitchen Leads"}
            return {"id": 77}
        return []

    with patch.object(orchestrator, "OPERATIONS", operations), patch.object(orchestrator, "call_api", side_effect=fake_call_api):
        response = orchestrator.run_orchestrator("Create manager group Kitchen Leads", "token", {})

    assert response == "Done — created schedule group Kitchen Leads (ID: 77)."


def test_run_orchestrator_prompts_for_name_when_message_only_says_create_schedule_group():
    operations = {"createScheduleGroup": "create-schedule-op"}

    with patch.object(orchestrator, "OPERATIONS", operations), patch.object(
        orchestrator, "call_api", side_effect=AssertionError("createScheduleGroup should not be called without a name")
    ):
        response = orchestrator.run_orchestrator("Can you create schedule group", "token", {})

    assert response == "What should I name the new schedule group?"
