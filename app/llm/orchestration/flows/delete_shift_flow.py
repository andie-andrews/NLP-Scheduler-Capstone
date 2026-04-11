from datetime import datetime


def handle_delete_shift_flow(
    *,
    message: str,
    token: str,
    session: dict,
    pending_delete_shift: dict | None,
    explicit_employee_id: int | None,
    operations: dict,
    call_api,
    format_shift_option_line,
    resolve_delete_shift_number_reply,
    clear_pending_delete_shift_state,
    is_delete_shift_intent,
    find_name_in_message,
    resolve_employee_id,
    set_pending_employee_disambiguation_state,
    build_employee_disambiguation_prompt,
    extract_weekday_date,
    week_range_from_date,
    set_pending_delete_shift_state,
    **_unused,
):
    if pending_delete_shift:
        selected_shift_id = resolve_delete_shift_number_reply(message, pending_delete_shift)
        if selected_shift_id is None:
            options = pending_delete_shift.get("options", [])
            option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(options)]
            return "Please reply with the shift number to delete:\n" + "\n".join(option_lines)
        if selected_shift_id is False:
            options = pending_delete_shift.get("options", [])
            option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(options)]
            return "That number is out of range. Please choose one of these:\n" + "\n".join(option_lines)

        delete_result = call_api(token, operations["deleteShift"], {"shiftId": selected_shift_id})
        clear_pending_delete_shift_state(session)
        return {
            "summary": f"Shift {selected_shift_id} deleted.",
            "data": {"deleteShiftResponse": delete_result, "deletedShiftId": selected_shift_id},
        }

    if not is_delete_shift_intent(message):
        return None

    employees = call_api(token, operations["searchEmployees"], {"query": ""})
    name = find_name_in_message(message, employees) if employees else None
    if explicit_employee_id:
        resolution = {"type": "resolved", "employeeId": explicit_employee_id}
    elif not name:
        return "Who should I delete the shift for?"
    else:
        resolution = resolve_employee_id(token, name, operations, call_api)
        if not resolution or resolution.get("type") == "not_found":
            return f"I couldn't find an employee matching '{name}'."
        if resolution.get("type") == "disambiguation":
            set_pending_employee_disambiguation_state(
                session,
                {
                    "name": name,
                    "options": resolution["raw"],
                    "original_message": message,
                },
            )
            return build_employee_disambiguation_prompt(name, resolution["raw"])

    target_date = extract_weekday_date(message)
    if not target_date:
        return "What day should I delete the shift from?"

    week_start_date, week_end_date = week_range_from_date(datetime.combine(target_date, datetime.min.time()))
    shifts = call_api(
        token,
        operations["getEmployeeShifts"],
        {
            "employeeId": resolution["employeeId"],
            "startDate": week_start_date.isoformat(),
            "endDate": week_end_date.isoformat(),
        },
    ) or []

    matching_day = [
        shift for shift in shifts
        if datetime.fromisoformat(shift["start"]).date() == target_date
    ]

    if not matching_day:
        return f"I couldn't find any shifts for {name.title()} on {target_date.strftime('%A, %b %d, %Y')}."

    if len(matching_day) == 1:
        shift_id = matching_day[0]["id"]
        delete_result = call_api(token, operations["deleteShift"], {"shiftId": shift_id})
        return {
            "summary": f"Deleted {name.title()}'s shift on {target_date.strftime('%A, %b %d, %Y')} (shiftId {shift_id}).",
            "data": {"deleteShiftResponse": delete_result, "deletedShiftId": shift_id},
        }

    state = {
        "intent": "delete_shift",
        "employeeId": resolution["employeeId"],
        "employeeName": name.title(),
        "targetDate": target_date.isoformat(),
        "options": matching_day,
    }
    set_pending_delete_shift_state(session, state)
    option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(matching_day)]
    return (
        f"I found multiple shifts for {name.title()} on {target_date.strftime('%A, %b %d, %Y')}. "
        "Reply with the number to delete:\n" + "\n".join(option_lines)
    )
