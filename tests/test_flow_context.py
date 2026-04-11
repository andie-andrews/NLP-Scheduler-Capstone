import unittest

from app.llm.orchestration.flow_context import (
    build_pending_flow_kwargs,
    build_shift_flow_kwargs,
)


class FlowContextTests(unittest.TestCase):
    def test_build_pending_flow_kwargs_contains_expected_keys(self):
        kwargs = build_pending_flow_kwargs(
            message="m",
            token="t",
            session={},
            pending_create_schedule=None,
            pending_delete_schedule=None,
            pending_employee_operation=None,
            operations={},
            call_api=lambda *_: None,
            clear_pending_create_schedule_state=lambda *_: None,
            clear_pending_delete_schedule_state=lambda *_: None,
            extract_schedule_name_or_id_from_message=lambda *_: None,
            normalize_schedule_id_arg=lambda *_: None,
            lookup_schedule_name_by_id=lambda *_: None,
            extract_employee_name_parts=lambda *_: (None, None),
            extract_role_id=lambda *_: None,
            extract_explicit_employee_id=lambda *_: None,
            resolve_employee_id=lambda *_: None,
            set_pending_employee_operation_state=lambda *_: None,
            clear_pending_employee_operation_state=lambda *_: None,
        )
        self.assertIn("pending_employee_operation", kwargs)
        self.assertIn("extract_schedule_name_or_id_from_message", kwargs)

    def test_build_shift_flow_kwargs_contains_expected_keys(self):
        kwargs = build_shift_flow_kwargs(
            message="m",
            token="t",
            session={},
            pending_shift=None,
            pending_delete_shift=None,
            pending_update_shift=None,
            explicit_employee_id=None,
            operations={},
            is_create_shift_intent=lambda *_: False,
            is_delete_shift_intent=lambda *_: False,
            is_update_shift_intent=lambda *_: False,
            find_name_in_message=lambda *_: None,
            resolve_employee_id=lambda *_: None,
            set_pending_employee_disambiguation_state=lambda *_: None,
            build_employee_disambiguation_prompt=lambda *_: "",
            extract_weekday_date=lambda *_: None,
            resolve_disambiguation_reply=lambda *_: None,
            attempt_fill_shift_state_from_message=lambda *_: None,
            build_create_shift_question=lambda *_: None,
            next_missing_shift_field=lambda *_: None,
            format_shift_option_line=lambda *_: "",
            resolve_delete_shift_number_reply=lambda *_: None,
            resolve_shift_number_reply=lambda *_: None,
            extract_time_of_day=lambda *_: None,
            extract_duration_hours=lambda *_: None,
            clear_pending_delete_shift_state=lambda *_: None,
            set_pending_delete_shift_state=lambda *_: None,
            clear_pending_update_shift_state=lambda *_: None,
            set_pending_update_shift_state=lambda *_: None,
            set_pending_shift_state=lambda *_: None,
            clear_pending_shift_state=lambda *_: None,
            normalize_schedule_id_arg=lambda *_: None,
            call_api=lambda *_: None,
            week_range_from_date=lambda *_: (None, None),
        )
        self.assertIn("pending_shift", kwargs)
        self.assertIn("resolve_shift_number_reply", kwargs)


if __name__ == "__main__":
    unittest.main()
