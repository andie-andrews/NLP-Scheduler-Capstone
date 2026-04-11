def handle_pending_schedule_flow(
    *,
    message: str,
    token: str,
    session: dict,
    pending_create_schedule: dict | None,
    pending_delete_schedule: dict | None,
    operations: dict,
    call_api,
    clear_pending_create_schedule_state,
    clear_pending_delete_schedule_state,
    extract_schedule_name_or_id_from_message,
    normalize_schedule_id_arg,
    lookup_schedule_name_by_id,
    **_unused,
):
    if pending_create_schedule:
        schedule_name = (message or "").strip()
        if not schedule_name:
            return "What should I name the new schedule?"
        result = call_api(token, operations["createSchedule"], {"name": schedule_name})
        clear_pending_create_schedule_state(session)
        schedule_id = result.get("id")
        if schedule_id is not None:
            return {"summary": f"Created schedule '{schedule_name}' (ID: {schedule_id}).", "data": {"scheduleId": schedule_id, "name": schedule_name}}
        return {"summary": f"Created schedule '{schedule_name}'.", "data": {"name": schedule_name, "createScheduleResponse": result}}

    if pending_delete_schedule:
        schedule_target = extract_schedule_name_or_id_from_message(message) or (message or "").strip()
        resolved_schedule_id = normalize_schedule_id_arg(token, schedule_target, operations, call_api)
        if resolved_schedule_id is None:
            return "I couldn't find that schedule. Which schedule should I delete?"
        delete_operation = operations.get("deleteSchedule")
        if not delete_operation:
            clear_pending_delete_schedule_state(session)
            return "Deleting schedules is not available because the API spec is missing deleteSchedule."
        call_api(token, delete_operation, {"scheduleId": resolved_schedule_id})
        clear_pending_delete_schedule_state(session)
        schedule_name = schedule_target if isinstance(schedule_target, str) else lookup_schedule_name_by_id(token, resolved_schedule_id)
        return f"Done — deleted schedule {schedule_name or resolved_schedule_id}."

    return None
