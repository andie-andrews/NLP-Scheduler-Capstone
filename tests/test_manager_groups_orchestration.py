import os
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")
from llm import orchestrator


def test_run_orchestrator_returns_manager_groups_listing():
    operations = {"getManagerScheduleGroups": "get-manager-groups-op"}

    def fake_call_api(_token, operation, args):
        if operation == "get-manager-groups-op":
            assert args == {"managerId": 7}
            return [{"id": 11, "name": "Manager"}, {"id": 22, "name": "Kitchen Leads"}]
        return []

    with patch.object(orchestrator, "OPERATIONS", operations), patch.object(orchestrator, "call_api", side_effect=fake_call_api):
        response = orchestrator.run_orchestrator("Show manager groups for managerId=7", "token", {})

    assert "Here are the manager groups" in response
    assert "1. Manager (ID: 11)" in response
    assert "2. Kitchen Leads (ID: 22)" in response
