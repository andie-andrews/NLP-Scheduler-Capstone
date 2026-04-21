import unittest
from unittest.mock import patch

from llm import orchestrator


class OrchestratorScheduleAssignmentTests(unittest.TestCase):
    def test_schedule_name_reply_does_not_auto_add_employee_to_schedule(self):
        state = {
            "intent": "create_shift",
            "employeeId": 101,
            "scheduleGroupId": None,
            "start": None,
            "pendingStartDate": None,
            "durationHours": None,
            "multiShiftDates": [],
            "awaiting": "schedule",
            "employee_options": [],
            "schedule_options": [],
            "employee_schedule_options": [],
            "available_schedule_options": [
                {"id": 5, "name": "Kitchen"},
                {"id": 8, "name": "Bartenders"},
            ],
        }
        calls = []

        def fake_call_api(_token, operation, args):
            calls.append((operation, args))
            if operation == "add-op":
                return {"__httpStatus": 200}
            return []

        with patch.object(orchestrator, "OPERATIONS", {"addEmployeeToScheduleGroup": "add-op"}), patch.object(
            orchestrator, "call_api", side_effect=fake_call_api
        ):
            result = orchestrator._attempt_fill_shift_state_from_message("Kitchen", "token", state)

        self.assertIsNone(result)
        self.assertIsNone(state["scheduleGroupId"])
        self.assertFalse(any(op == "add-op" for op, _ in calls))

    def test_numeric_schedule_not_assigned_without_membership_or_add_flow(self):
        state = {
            "intent": "create_shift",
            "employeeId": 101,
            "scheduleGroupId": None,
            "start": None,
            "pendingStartDate": None,
            "durationHours": None,
            "multiShiftDates": [],
            "awaiting": "schedule",
            "employee_options": [],
            "schedule_options": [],
            "employee_schedule_options": [],
            "available_schedule_options": [],
        }

        with patch.object(orchestrator, "OPERATIONS", {}), patch.object(orchestrator, "call_api", return_value=[]):
            result = orchestrator._attempt_fill_shift_state_from_message("4", "token", state)

        self.assertIsNone(result)
        self.assertIsNone(state["scheduleGroupId"])

    def test_single_employee_schedule_is_auto_selected(self):
        state = {
            "intent": "create_shift",
            "employeeId": 101,
            "scheduleGroupId": None,
            "start": None,
            "pendingStartDate": None,
            "durationHours": None,
            "multiShiftDates": [],
            "awaiting": "schedule",
            "employee_options": [],
            "schedule_options": [],
            "employee_schedule_options": [{"id": 8, "name": "Bartenders"}],
            "available_schedule_options": [{"id": 8, "name": "Bartenders"}],
        }

        with patch.object(orchestrator, "OPERATIONS", {}), patch.object(orchestrator, "call_api", return_value=[]):
            result = orchestrator._attempt_fill_shift_state_from_message("1", "token", state)

        self.assertIsNone(result)
        self.assertEqual(state["scheduleGroupId"], 8)


if __name__ == "__main__":
    unittest.main()
