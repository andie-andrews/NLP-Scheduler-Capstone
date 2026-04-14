import unittest
from unittest.mock import patch

from llm import orchestrator


class OrchestratorScheduleAssignmentTests(unittest.TestCase):
    def test_schedule_name_reply_adds_employee_to_schedule(self):
        state = {
            "intent": "create_shift",
            "employeeId": 101,
            "scheduleId": None,
            "start": None,
            "pendingStartDate": None,
            "durationHours": None,
            "multiShiftDates": [],
            "awaiting": "add_to_schedule_confirmation",
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

        with patch.object(orchestrator, "OPERATIONS", {"addEmployeeToSchedule": "add-op"}), patch.object(
            orchestrator, "call_api", side_effect=fake_call_api
        ):
            result = orchestrator._attempt_fill_shift_state_from_message("Kitchen", "token", state)

        self.assertIsNone(result)
        self.assertEqual(state["scheduleId"], 5)
        self.assertEqual(
            state["recent_schedule_assignment"],
            {"employeeName": None, "scheduleName": "Kitchen", "scheduleId": 5},
        )
        self.assertIn(("add-op", {"scheduleId": 5, "employeeId": 101}), calls)

    def test_numeric_schedule_not_assigned_without_membership_or_add_flow(self):
        state = {
            "intent": "create_shift",
            "employeeId": 101,
            "scheduleId": None,
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
        self.assertIsNone(state["scheduleId"])


if __name__ == "__main__":
    unittest.main()
