import unittest
from datetime import date

from app.llm.orchestration.flows.create_shift_flow import handle_create_shift_flow
from app.llm.orchestration.flows.delete_shift_flow import handle_delete_shift_flow
from app.llm.orchestration.flows.update_shift_flow import handle_update_shift_flow


class ShiftFlowSmokeTests(unittest.TestCase):
    def test_create_shift_flow_returns_none_when_not_applicable(self):
        result = handle_create_shift_flow(
            message="hello",
            token="t",
            session={},
            pending_shift=None,
            operations={},
            is_create_shift_intent=lambda *_: False,
            resolve_disambiguation_reply=lambda *_: None,
            attempt_fill_shift_state_from_message=lambda *_: None,
            build_create_shift_question=lambda *_: None,
            next_missing_shift_field=lambda *_: None,
            set_pending_shift_state=lambda *_: None,
            clear_pending_shift_state=lambda *_: None,
            normalize_schedule_id_arg=lambda *_: None,
            call_api=lambda *_: None,
            week_range_from_date=lambda *_: (None, None),
        )
        self.assertIsNone(result)

    def test_delete_shift_flow_returns_none_when_not_applicable(self):
        result = handle_delete_shift_flow(
            message="hello",
            token="t",
            session={},
            pending_delete_shift=None,
            explicit_employee_id=None,
            operations={},
            call_api=lambda *_: None,
            format_shift_option_line=lambda *_: "",
            resolve_delete_shift_number_reply=lambda *_: None,
            clear_pending_delete_shift_state=lambda *_: None,
            is_delete_shift_intent=lambda *_: False,
            find_name_in_message=lambda *_: None,
            resolve_employee_id=lambda *_: None,
            set_pending_employee_disambiguation_state=lambda *_: None,
            build_employee_disambiguation_prompt=lambda *_: "",
            extract_weekday_date=lambda *_: None,
            week_range_from_date=lambda *_: (None, None),
            set_pending_delete_shift_state=lambda *_: None,
        )
        self.assertIsNone(result)

    def test_update_shift_flow_returns_none_when_not_applicable(self):
        result = handle_update_shift_flow(
            message="hello",
            token="t",
            session={},
            pending_update_shift=None,
            explicit_employee_id=None,
            operations={},
            call_api=lambda *_: None,
            extract_weekday_date=lambda *_: None,
            week_range_from_date=lambda *_: (None, None),
            format_shift_option_line=lambda *_: "",
            resolve_shift_number_reply=lambda *_: None,
            extract_time_of_day=lambda *_: None,
            extract_duration_hours=lambda *_: None,
            clear_pending_update_shift_state=lambda *_: None,
            set_pending_update_shift_state=lambda *_: None,
            is_update_shift_intent=lambda *_: False,
            find_name_in_message=lambda *_: None,
            resolve_employee_id=lambda *_: None,
            set_pending_employee_disambiguation_state=lambda *_: None,
            build_employee_disambiguation_prompt=lambda *_: "",
        )
        self.assertIsNone(result)

    def test_create_shift_flow_creates_multiple_shifts_when_dates_are_present(self):
        calls = []
        responses = [{"id": 1}, {"id": 2}]

        def fake_call_api(_token, operation, args):
            if operation == "create-shift-op":
                calls.append(args)
                return responses[len(calls) - 1]
            return []

        session = {}
        result = handle_create_shift_flow(
            message="schedule jane next week monday-friday 9am-5pm",
            token="t",
            session=session,
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleId": 22,
                "start": "2026-04-20T09:00:00",
                "pendingStartDate": None,
                "durationHours": 8,
                "multiShiftDates": ["2026-04-20", "2026-04-21"],
                "awaiting": None,
                "employee_options": [],
                "schedule_options": [],
            },
            operations={"createShift": "create-shift-op"},
            is_create_shift_intent=lambda *_: True,
            resolve_disambiguation_reply=lambda *_: None,
            attempt_fill_shift_state_from_message=lambda *_: None,
            build_create_shift_question=lambda *_: None,
            next_missing_shift_field=lambda *_: None,
            set_pending_shift_state=lambda *_: None,
            clear_pending_shift_state=lambda *_: None,
            normalize_schedule_id_arg=lambda *_: 22,
            call_api=fake_call_api,
            week_range_from_date=lambda *_: (None, None),
        )

        self.assertEqual(result["summary"], "Shifts created successfully (2 new).")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["start"], "2026-04-20T09:00:00")
        self.assertEqual(calls[1]["start"], "2026-04-21T09:00:00")

    def test_create_shift_flow_skips_existing_recurring_shifts(self):
        create_calls = []

        def fake_call_api(_token, operation, args):
            if operation == "get-shifts-op":
                return [
                    {"employeeId": 10, "start": "2026-04-20T09:00:00", "durationHours": 8},
                    {"employeeId": 10, "start": "2026-04-21T09:00:00", "durationHours": 8},
                ]
            if operation == "create-shift-op":
                create_calls.append(args)
                return {"id": 99}
            return []

        result = handle_create_shift_flow(
            message="schedule jane next week monday-friday 9am-5pm",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleId": 22,
                "start": "2026-04-20T09:00:00",
                "pendingStartDate": None,
                "durationHours": 8,
                "multiShiftDates": ["2026-04-20", "2026-04-21"],
                "awaiting": None,
                "employee_options": [],
                "schedule_options": [],
            },
            operations={"createShift": "create-shift-op", "getScheduleShifts": "get-shifts-op"},
            is_create_shift_intent=lambda *_: True,
            resolve_disambiguation_reply=lambda *_: None,
            attempt_fill_shift_state_from_message=lambda *_: None,
            build_create_shift_question=lambda *_: None,
            next_missing_shift_field=lambda *_: None,
            set_pending_shift_state=lambda *_: None,
            clear_pending_shift_state=lambda *_: None,
            normalize_schedule_id_arg=lambda *_: 22,
            call_api=fake_call_api,
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertEqual(result["summary"], "All requested shifts already exist on that schedule.")
        self.assertEqual(len(create_calls), 0)


if __name__ == "__main__":
    unittest.main()
