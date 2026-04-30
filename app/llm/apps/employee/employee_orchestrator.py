from __future__ import annotations

from llm.apps.scheduling.schedule_orchestrator import (
    OPERATIONS,
    _extract_employee_name_parts,
    _extract_explicit_employee_id,
    _extract_role_id,
)
from llm.openapi_client import call_api
from llm.orchestration.apps.employee.flows.pending_employee_flow import handle_pending_employee_flow
from llm.orchestration.resolvers import resolve_employee_id
from llm.orchestration.state_store import (
    clear_pending_employee_operation_state,
    get_pending_employee_operation_state,
    set_pending_employee_operation_state,
)


def run_employee_orchestrator(message: str, token: str, session: dict):
    """Employee-domain orchestrator entrypoint.

    Handles employee pending-operation workflows so employee flow logic is owned by
    the employee app namespace and can be invoked from cross-domain routes.
    """
    session["orchestrator_domain"] = "employee"
    pending_employee_operation = get_pending_employee_operation_state(session)
    return handle_pending_employee_flow(
        message=message,
        token=token,
        session=session,
        pending_employee_operation=pending_employee_operation,
        operations=OPERATIONS,
        call_api=call_api,
        extract_employee_name_parts=_extract_employee_name_parts,
        extract_role_id=_extract_role_id,
        extract_explicit_employee_id=_extract_explicit_employee_id,
        resolve_employee_id=resolve_employee_id,
        set_pending_employee_operation_state=set_pending_employee_operation_state,
        clear_pending_employee_operation_state=clear_pending_employee_operation_state,
    )
