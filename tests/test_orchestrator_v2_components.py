import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from llm.orchestrator_v2_components.intents import is_create_shift_intent, is_delete_shift_intent
from llm.orchestrator_v2_components.parsers import (
    extract_duration_hours,
    extract_schedule_name,
    extract_weekday_date,
    extract_weekday_datetime,
    find_name_in_message,
    format_shift_option_line,
    get_week_start,
    week_start_from_iso,
)
from llm.orchestrator_v2_components.resolvers import (
    normalize_schedule_id_arg,
    resolve_employee_id,
    resolve_schedule_id,
)
from llm.orchestrator_v2_components.state_store import (
    clear_pending_delete_shift_state,
    clear_pending_shift_state,
    get_pending_delete_shift_state,
    get_pending_shift_state,
    set_pending_delete_shift_state,
    set_pending_shift_state,
)
from llm.orchestrator_v2_components.summary import summarize_shifts
from llm.orchestrator_v2_components.tools import build_tools, sanitize_tools_for_openai


class TestIntents(unittest.TestCase):
    def test_create_shift_intent_keyword_and_fallback(self):
        self.assertTrue(is_create_shift_intent("Please create shift for Alex"))
        self.assertTrue(is_create_shift_intent("can you schedule a shift tomorrow"))
        self.assertFalse(is_create_shift_intent("show me my schedule"))

    def test_delete_shift_intent(self):
        self.assertTrue(is_delete_shift_intent("delete my shift on friday"))
        self.assertFalse(is_delete_shift_intent("delete my availability"))


class TestParsers(unittest.TestCase):
    def test_extractors(self):
        self.assertEqual(extract_duration_hours("for 6 hours"), 6)
        self.assertIsNone(extract_duration_hours("for a while"))
        self.assertEqual(extract_schedule_name("put this on retail schedule"), "retail")

    def test_find_name_in_message(self):
        employees = [{"firstName": "Alex", "lastName": "Smith"}, {"firstName": "Sam", "lastName": "Lee"}]
        self.assertEqual(find_name_in_message("schedule Alex Smith tomorrow", employees), "alex smith")
        self.assertEqual(find_name_in_message("schedule sam tomorrow", employees), "sam")

    @patch("llm.orchestrator_v2_components.parsers.datetime")
    def test_weekday_date_time_parsing(self, mock_datetime):
        fake_now = datetime(2026, 4, 6, 10, 0, 0)  # Monday
        mock_datetime.now.return_value = fake_now
        mock_datetime.today.return_value = fake_now
        mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x)

        iso = extract_weekday_datetime("next friday at 8am")
        self.assertTrue(iso.startswith("2026-04-17T08:00:00"))

        target_date = extract_weekday_date("this wednesday")
        self.assertEqual(target_date.isoformat(), "2026-04-08")

        self.assertEqual(get_week_start(), "04/06/2026")
        self.assertEqual(week_start_from_iso("2026-04-10T08:00:00"), "04/06/2026")

    def test_format_shift_option_line(self):
        value = format_shift_option_line(1, {"start": "2026-04-10T09:00:00", "durationHours": 8})
        self.assertIn("1.", value)
        self.assertIn("8 hours", value)


class TestResolvers(unittest.TestCase):
    def test_resolve_employee_and_schedule(self):
        operations = {"searchEmployees": {"id": "searchEmployees"}, "getSchedules": {"id": "getSchedules"}}

        def api_caller(_token, op, args):
            if op["id"] == "searchEmployees":
                if args["query"] == "alex":
                    return [{"id": 3, "firstName": "Alex", "lastName": "Smith"}]
                return []
            if op["id"] == "getSchedules":
                return [{"id": 10, "name": "Retail"}, {"id": 11, "name": "Pharmacy"}]
            return []

        self.assertEqual(resolve_employee_id("t", "alex", operations, api_caller)["employeeId"], 3)
        self.assertEqual(resolve_schedule_id("t", "retail", operations, api_caller)["scheduleId"], 10)
        self.assertEqual(normalize_schedule_id_arg("t", "11", operations, api_caller), 11)
        self.assertEqual(normalize_schedule_id_arg("t", "pharmacy", operations, api_caller), 11)


class DummyMemory:
    pass


class TestStateStore(unittest.TestCase):
    def test_state_roundtrip(self):
        session = {"memory": DummyMemory()}
        self.assertIsNone(get_pending_shift_state(session))

        set_pending_shift_state(session, {"intent": "create_shift"})
        self.assertEqual(get_pending_shift_state(session)["intent"], "create_shift")
        clear_pending_shift_state(session)
        self.assertIsNone(get_pending_shift_state(session))

        set_pending_delete_shift_state(session, {"intent": "delete_shift"})
        self.assertEqual(get_pending_delete_shift_state(session)["intent"], "delete_shift")
        clear_pending_delete_shift_state(session)
        self.assertIsNone(get_pending_delete_shift_state(session))


class TestToolsAndSummary(unittest.TestCase):
    def test_build_and_sanitize_tools(self):
        operations = {
            "createShift": {
                "summary": "Create shift",
                "parameters": [{"name": "scheduleId", "required": True, "schema": {"type": "integer"}}],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {"scheduleId": {"type": "integer"}, "employeeId": {"type": "integer"}},
                                "required": ["scheduleId", "employeeId"],
                            }
                        }
                    }
                },
            }
        }
        tools = build_tools(operations)
        sanitized = sanitize_tools_for_openai(tools)
        required = sanitized[0]["function"]["parameters"]["required"]
        self.assertEqual(required, ["scheduleId", "employeeId"])

    def test_summarize_shifts(self):
        shifts = [
            {"start": "2026-04-11T08:00:00", "durationHours": 4},
            {"start": "2026-04-12T08:00:00", "durationHours": 6},
        ]
        summary = summarize_shifts(shifts, "how many hours do I have")
        self.assertEqual(summary["totalHours"], 10)
        self.assertIn("Total scheduled hours", summary["summary"])


if __name__ == "__main__":
    unittest.main()
