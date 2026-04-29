import unittest
from datetime import date
from unittest.mock import Mock

from llm.orchestration.apps.scheduling.flows.create_shift_flow import handle_create_shift_flow
from llm.orchestration.apps.scheduling.flows.delete_shift_flow import handle_delete_shift_flow
from llm.orchestration.apps.scheduling.flows.update_shift_flow import handle_update_shift_flow


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

    def test_update_shift_flow_patches_duration_and_employee_reassignment(self):
        api_calls = []

        def fake_call_api(_token, operation, args):
            api_calls.append((operation, args))
            if operation == "search-op":
                return [
                    {"id": 10, "firstName": "John", "lastName": "Doe"},
                    {"id": 11, "firstName": "Jane", "lastName": "Doe"},
                ]
            return {"ok": True}

        result = handle_update_shift_flow(
            message="reassign shift to jane and set duration to 8 hours",
            token="t",
            session={"role": "Supervisor"},
            pending_update_shift={
                "intent": "update_shift",
                "employeeId": 10,
                "employeeName": "john",
                "targetDate": "2026-04-20",
                "shiftId": 5,
                "selectedShift": {"id": 5, "start": "2026-04-20T09:00:00"},
                "options": [],
            },
            explicit_employee_id=None,
            operations={"searchEmployees": "search-op"},
            call_api=fake_call_api,
            extract_weekday_date=lambda *_: None,
            week_range_from_date=lambda *_: (None, None),
            format_shift_option_line=lambda *_: "",
            resolve_shift_number_reply=lambda *_: None,
            extract_time_of_day=lambda *_: None,
            extract_duration_hours=lambda *_: 8,
            clear_pending_update_shift_state=lambda *_: None,
            set_pending_update_shift_state=lambda *_: None,
            is_update_shift_intent=lambda *_: True,
            find_name_in_message=lambda *_: None,
            resolve_employee_id=lambda *_args, **_kwargs: {"employeeId": 11},
            set_pending_employee_disambiguation_state=lambda *_: None,
            build_employee_disambiguation_prompt=lambda *_: "",
        )

        self.assertEqual(result["summary"], "Shift 5 updated.")
        update_operation, payload = api_calls[-1]
        self.assertEqual(update_operation["method"], "PATCH")
        self.assertEqual(payload["shiftId"], 5)
        self.assertEqual(payload["durationHours"], 8)
        self.assertEqual(payload["employeeId"], 11)

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
                "scheduleGroupId": 22,
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

        self.assertEqual(
            result["summary"],
            "2 shifts created for employee 10 from 9:00 AM to 5:00 PM (April 20, 2026 to April 21, 2026).",
        )
        self.assertEqual(result["data"]["failedCount"], 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["start"], "2026-04-20T09:00:00")
        self.assertEqual(calls[1]["start"], "2026-04-21T09:00:00")

    def test_create_shift_flow_summarizes_weekly_recurring_multi_create(self):
        calls = []

        def fake_call_api(_token, operation, args):
            if operation == "create-shift-op":
                calls.append(args)
                return {"id": len(calls)}
            return []

        result = handle_create_shift_flow(
            message="create shift every monday for next 3 weeks",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleGroupId": 22,
                "start": "2026-04-20T09:00:00",
                "pendingStartDate": None,
                "durationHours": 8,
                "multiShiftDates": ["2026-04-20", "2026-04-27", "2026-05-04"],
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
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertEqual(
            result["summary"],
            "3 weekly shifts created for employee 10 every Monday from 9:00 AM to 5:00 PM (April 20, 2026 to May 4, 2026).",
        )
        self.assertEqual(result["data"]["failedCount"], 0)

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
                "scheduleGroupId": 22,
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

    def test_create_shift_flow_single_shift_still_creates_even_if_match_exists(self):
        create_calls = []

        def fake_call_api(_token, operation, args):
            if operation == "get-shifts-op":
                return [{"employeeId": 10, "start": "2026-04-20T09:00:00", "durationHours": 8}]
            if operation == "create-shift-op":
                create_calls.append(args)
                return {"id": 100}
            return []

        result = handle_create_shift_flow(
            message="create shift",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleGroupId": 22,
                "start": "2026-04-20T09:00:00",
                "pendingStartDate": None,
                "durationHours": 8,
                "multiShiftDates": [],
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

        self.assertEqual(
            result["summary"],
            "Shift created for employee 10 on April 20, 2026 from 9:00 AM to 5:00 PM.",
        )
        self.assertEqual(len(create_calls), 1)
        self.assertEqual(result["data"]["createdCount"], 1)
        self.assertEqual(result["data"]["failedCount"], 0)
        self.assertEqual(result["data"]["createShiftResponse"], {"id": 100})

    def test_create_shift_flow_reports_partial_validation_failures(self):
        def fake_call_api(_token, operation, _args):
            if operation == "create-shift-op":
                fake_call_api.calls += 1
                if fake_call_api.calls == 1:
                    return {"id": 123, "__httpStatus": 200}
                return {
                    "title": "One or more validation errors occurred.",
                    "errors": {
                        "overlapping_shift": ["Shift overlaps existing shift."]
                    },
                    "__httpStatus": 400,
                }
            return []

        fake_call_api.calls = 0

        result = handle_create_shift_flow(
            message="create recurring shifts",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleGroupId": 22,
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
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertIn("could not be created", result["summary"])
        self.assertEqual(result["data"]["createdCount"], 1)
        self.assertEqual(result["data"]["failedCount"], 1)
        self.assertEqual(result["data"]["failedShifts"][0]["statusCode"], 400)

    def test_create_shift_flow_treats_success_false_payload_as_failure(self):
        def fake_call_api(_token, operation, _args):
            if operation == "create-shift-op":
                return {
                    "success": False,
                    "errors": [{"code": "overlapping_shift", "message": "Shift overlaps existing shift."}],
                    "__httpStatus": 200,
                }
            return []

        result = handle_create_shift_flow(
            message="create shift",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleGroupId": 22,
                "start": "2026-04-20T09:00:00",
                "pendingStartDate": None,
                "durationHours": 8,
                "multiShiftDates": [],
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
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertEqual(result["data"]["createdCount"], 0)
        self.assertEqual(result["data"]["failedCount"], 1)
        self.assertIn("No shifts were created", result["summary"])

    def test_create_shift_flow_returns_direct_reply_from_state_fill(self):
        clear_pending_shift_state = Mock()
        result = handle_create_shift_flow(
            message="no",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleGroupId": None,
                "start": None,
                "pendingStartDate": None,
                "durationHours": None,
                "multiShiftDates": [],
                "awaiting": "add_to_schedule_confirmation",
                "employee_options": [],
                "schedule_options": [],
            },
            operations={"createShift": "create-shift-op"},
            is_create_shift_intent=lambda *_: True,
            resolve_disambiguation_reply=lambda *_: None,
            attempt_fill_shift_state_from_message=lambda *_: {
                "type": "reply",
                "message": "Okay — I won't create a shift until the employee is assigned to a schedule.",
            },
            build_create_shift_question=lambda *_: None,
            next_missing_shift_field=lambda *_: None,
            set_pending_shift_state=lambda *_: None,
            clear_pending_shift_state=clear_pending_shift_state,
            normalize_schedule_id_arg=lambda *_: 22,
            call_api=lambda *_: {},
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertEqual(
            result,
            "Okay — I won't create a shift until the employee is assigned to a schedule.",
        )
        clear_pending_shift_state.assert_called_once()

    def test_create_shift_flow_surfaces_assignment_notice_before_next_question(self):
        session = {}
        result = handle_create_shift_flow(
            message="2",
            token="t",
            session=session,
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "employeeName": "Sophia",
                "scheduleGroupId": 4,
                "start": "2026-04-15T09:00:00",
                "pendingStartDate": None,
                "durationHours": None,
                "multiShiftDates": [],
                "awaiting": "add_to_schedule_selection",
                "employee_options": [],
                "schedule_options": [],
                "recent_schedule_assignment": {
                    "employeeName": "Sophia",
                    "scheduleName": "Hostesses",
                    "scheduleGroupId": 4,
                },
            },
            operations={"createShift": "create-shift-op"},
            is_create_shift_intent=lambda *_: True,
            resolve_disambiguation_reply=lambda *_: None,
            attempt_fill_shift_state_from_message=lambda *_: None,
            build_create_shift_question=lambda *_: "How long should the shift be (in hours)?",
            next_missing_shift_field=lambda *_: "duration",
            set_pending_shift_state=lambda *_: None,
            clear_pending_shift_state=lambda *_: None,
            normalize_schedule_id_arg=lambda *_: 4,
            call_api=lambda *_: {},
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertEqual(
            result,
            "Done — I added Sophia to Hostesses.\n\nHow long should the shift be (in hours)?",
        )

    def test_create_shift_flow_surfaces_non_overlap_validation_message(self):
        def fake_call_api(_token, operation, _args):
            if operation == "create-shift-op":
                return {
                    "success": False,
                    "errors": [
                        {
                            "code": "employee_not_assigned_to_schedule",
                            "message": "Employee is not assigned to this schedule.",
                        }
                    ],
                    "__httpStatus": 400,
                }
            return []

        result = handle_create_shift_flow(
            message="create shift",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleGroupId": 22,
                "start": "2026-04-20T09:00:00",
                "pendingStartDate": None,
                "durationHours": 8,
                "multiShiftDates": [],
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
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertEqual(result["data"]["createdCount"], 0)
        self.assertEqual(result["data"]["failedCount"], 1)
        self.assertEqual(
            result["data"]["failedShifts"][0]["error"],
            "Employee is not assigned to this schedule.",
        )

    def test_create_shift_flow_surfaces_first_raw_error_line(self):
        def fake_call_api(_token, operation, _args):
            if operation == "create-shift-op":
                return {
                    "statusCode": 500,
                    "rawText": "System.InvalidOperationException: Invalid operation. The connection is closed.\nstack trace...",
                    "__httpStatus": 500,
                }
            return []

        result = handle_create_shift_flow(
            message="create shift",
            token="t",
            session={},
            pending_shift={
                "intent": "create_shift",
                "employeeId": 10,
                "scheduleGroupId": 22,
                "start": "2026-04-20T09:00:00",
                "pendingStartDate": None,
                "durationHours": 8,
                "multiShiftDates": [],
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
            week_range_from_date=lambda *_: (date(2026, 4, 19), date(2026, 4, 25)),
        )

        self.assertEqual(result["data"]["createdCount"], 0)
        self.assertEqual(result["data"]["failedCount"], 1)
        self.assertEqual(
            result["data"]["failedShifts"][0]["error"],
            "System.InvalidOperationException: Invalid operation. The connection is closed.",
        )


if __name__ == "__main__":
    unittest.main()
