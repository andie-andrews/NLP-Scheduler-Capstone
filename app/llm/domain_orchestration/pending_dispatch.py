from __future__ import annotations

from llm.orchestration.state_store import (
    get_pending_delete_shift_state,
    get_pending_create_schedule_state,
    get_pending_delete_schedule_state,
    get_pending_employee_operation_state,
    get_pending_schedule_member_change_state,
    get_pending_shift_state,
    get_pending_show_shifts_state,
    get_pending_update_shift_state,
)


def dispatch_pending_before_plugin(*, domain: str, message: str, token: str, session: dict):
    """Dispatch domain-specific pending workflows before plugin runtime execution."""
    if domain == "schedule":
        has_pending_schedule_state = any(
            [
                get_pending_shift_state(session),
                get_pending_delete_shift_state(session),
                get_pending_show_shifts_state(session),
                get_pending_update_shift_state(session),
                get_pending_schedule_member_change_state(session),
                get_pending_create_schedule_state(session),
                get_pending_delete_schedule_state(session),
                get_pending_employee_operation_state(session),
            ]
        )
        if not has_pending_schedule_state:
            return None

        from llm.domain_orchestration.domains.scheduling.plugins.schedule_orchestrator import dispatch_pending_flows

        return dispatch_pending_flows(message=message, token=token, session=session)

    if domain == "employee":
        if get_pending_employee_operation_state(session) is None:
            return None

        from llm.domain_orchestration.domains.employee.plugins.employee_orchestrator import run_employee_orchestrator

        return run_employee_orchestrator(message=message, token=token, session=session)

    return None
