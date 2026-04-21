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
    extract_schedule_name_for_create=None,
    **_unused,
):
    if pending_create_schedule:
        create_operation = operations.get("createScheduleGroup")
        if not create_operation:
            clear_pending_create_schedule_state(session)
            return "Schedule-group creation is not available because the API spec is missing createScheduleGroup."

        schedule_name = None
        if callable(extract_schedule_name_for_create):
            schedule_name = extract_schedule_name_for_create(message)
        if not schedule_name:
            schedule_name = (message or "").strip() or pending_create_schedule.get("name")
        if not schedule_name:
            return "What should I name the new schedule group?"

        created = call_api(token, create_operation, {"name": schedule_name}) or {}
        clear_pending_create_schedule_state(session)
        created_id = created.get("id") if isinstance(created, dict) else None
        return (
            f"Done — created schedule group {schedule_name} (ID: {created_id})."
            if created_id is not None
            else f"Done — created schedule group {schedule_name}."
        )

    if pending_delete_schedule:
        schedule_target = extract_schedule_name_or_id_from_message(message) or (message or "").strip()
        resolved_schedule_id = normalize_schedule_id_arg(token, schedule_target, operations, call_api)
        if resolved_schedule_id is None:
            return "I couldn't find that schedule. Which schedule should I delete?"
        delete_operation = operations.get("deleteScheduleGroup")
        if not delete_operation:
            clear_pending_delete_schedule_state(session)
            return "Deleting schedule groups is not available because the API spec is missing deleteScheduleGroup."
        call_api(token, delete_operation, {"scheduleGroupId": resolved_schedule_id})
        clear_pending_delete_schedule_state(session)
        schedule_name = schedule_target if isinstance(schedule_target, str) else lookup_schedule_name_by_id(token, resolved_schedule_id)
        return f"Done — deleted schedule group {schedule_name or resolved_schedule_id}."

    return None
