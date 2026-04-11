import unittest

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


if __name__ == "__main__":
    unittest.main()
