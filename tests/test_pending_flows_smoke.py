import unittest

from app.llm.orchestration.flows.pending_schedule_flow import handle_pending_schedule_flow
from app.llm.orchestration.flows.pending_employee_flow import handle_pending_employee_flow


class PendingFlowSmokeTests(unittest.TestCase):
    def test_pending_schedule_flow_returns_none_when_no_pending_state(self):
        result = handle_pending_schedule_flow(
            message="hello",
            token="t",
            session={},
            pending_create_schedule=None,
            pending_delete_schedule=None,
            operations={},
            call_api=lambda *_: None,
            clear_pending_create_schedule_state=lambda *_: None,
            clear_pending_delete_schedule_state=lambda *_: None,
            extract_schedule_name_or_id_from_message=lambda *_: None,
            normalize_schedule_id_arg=lambda *_: None,
            lookup_schedule_name_by_id=lambda *_: None,
        )
        self.assertIsNone(result)

    def test_pending_employee_flow_returns_none_when_no_pending_state(self):
        result = handle_pending_employee_flow(
            message="hello",
            token="t",
            session={},
            pending_employee_operation=None,
            operations={},
            call_api=lambda *_: None,
            extract_employee_name_parts=lambda *_: (None, None),
            extract_role_id=lambda *_: None,
            extract_explicit_employee_id=lambda *_: None,
            resolve_employee_id=lambda *_: None,
            set_pending_employee_operation_state=lambda *_: None,
            clear_pending_employee_operation_state=lambda *_: None,
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
