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
        clear_pending_create_schedule_state(session)
        return "Schedule creation is only available in the Manage Schedules UI."

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
