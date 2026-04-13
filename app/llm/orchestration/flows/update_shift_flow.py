from datetime import datetime


def handle_update_shift_flow(
    *,
    message: str,
    token: str,
    session: dict,
    pending_update_shift: dict | None,
    explicit_employee_id: int | None,
    operations: dict,
    call_api,
    extract_weekday_date,
    week_range_from_date,
    format_shift_option_line,
    resolve_shift_number_reply,
    extract_time_of_day,
    extract_duration_hours,
    clear_pending_update_shift_state,
    set_pending_update_shift_state,
    is_update_shift_intent,
    find_name_in_message,
    resolve_employee_id,
    set_pending_employee_disambiguation_state,
    build_employee_disambiguation_prompt,
    **_unused,
):
    if pending_update_shift:
        if not pending_update_shift.get("targetDate"):
            target_date = extract_weekday_date(message)
            if not target_date:
                return "What day is the shift you want to update?"
            pending_update_shift["targetDate"] = target_date.isoformat()

        if not pending_update_shift.get("shiftId"):
            if not pending_update_shift.get("options"):
                target_date = datetime.fromisoformat(pending_update_shift["targetDate"]).date()
                week_start_date, week_end_date = week_range_from_date(datetime.combine(target_date, datetime.min.time()))
                shifts = call_api(
                    token,
                    operations["getEmployeeShifts"],
                    {
                        "employeeId": pending_update_shift["employeeId"],
                        "startDate": week_start_date.isoformat(),
                        "endDate": week_end_date.isoformat(),
                    },
                ) or []
                matching_day = [
                    shift for shift in shifts
                    if datetime.fromisoformat(shift["start"]).date() == target_date
                ]
                if not matching_day:
                    pending_update_shift["targetDate"] = None
                    set_pending_update_shift_state(session, pending_update_shift)
                    return f"I couldn't find any shifts on {target_date.strftime('%A, %b %d, %Y')}. What day should I check instead?"
                if len(matching_day) == 1:
                    pending_update_shift["shiftId"] = matching_day[0]["id"]
                    pending_update_shift["selectedShift"] = matching_day[0]
                else:
                    pending_update_shift["options"] = matching_day
                    set_pending_update_shift_state(session, pending_update_shift)
                    option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(matching_day)]
                    return (
                        f"I found multiple shifts on {target_date.strftime('%A, %b %d, %Y')}. "
                        "Reply with the number to update:\n" + "\n".join(option_lines)
                    )
            else:
                selected_shift = resolve_shift_number_reply(message, pending_update_shift)
                if selected_shift is None:
                    option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(pending_update_shift.get("options", []))]
                    return "Please reply with the shift number to update:\n" + "\n".join(option_lines)
                if selected_shift is False:
                    option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(pending_update_shift.get("options", []))]
                    return "That number is out of range. Please choose one of these:\n" + "\n".join(option_lines)
                pending_update_shift["shiftId"] = selected_shift["id"]
                pending_update_shift["selectedShift"] = selected_shift
                pending_update_shift["options"] = []

        update_start = None
        selected_shift = pending_update_shift.get("selectedShift")
        if selected_shift:
            selected_date = datetime.fromisoformat(selected_shift["start"]).date()
            parsed_time = extract_time_of_day(message)
            if parsed_time:
                update_start = datetime.combine(selected_date, datetime.min.time()).replace(
                    hour=parsed_time[0],
                    minute=parsed_time[1],
                ).isoformat()

        update_duration = extract_duration_hours(message)
        if not update_start and not update_duration:
            set_pending_update_shift_state(session, pending_update_shift)
            return "What should I update for this shift? Please provide a new time, duration in hours, or both."

        payload = {"shiftId": pending_update_shift["shiftId"]}
        if update_start:
            payload["start"] = update_start
        if update_duration:
            payload["durationHours"] = update_duration

        update_operation = {
            "method": "PUT",
            "path": "/api/shifts/{shiftId}",
            "parameters": [
                {"name": "shiftId", "in": "path", "required": True, "schema": {"type": "integer"}},
            ],
            "requestBody": None,
            "summary": "Update shift",
        }
        update_result = call_api(token, update_operation, payload)
        clear_pending_update_shift_state(session)
        return {
            "summary": f"Shift {payload['shiftId']} updated.",
            "data": {"updateShiftResponse": update_result, "updatedShift": payload},
        }

    if not is_update_shift_intent(message):
        return None

    target_employee_id = explicit_employee_id or session.get("employee_id")
    name = None
    if not explicit_employee_id and session.get("role") != "Employee":
        employees = call_api(token, operations["searchEmployees"], {"query": ""})
        name = find_name_in_message(message, employees) if employees else None
        if name:
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
            target_employee_id = resolution["employeeId"]

    if not target_employee_id:
        return "Who should I update the shift for?"

    target_date = extract_weekday_date(message)
    update_state = {
        "intent": "update_shift",
        "employeeId": target_employee_id,
        "employeeName": name.title() if name else "you",
        "targetDate": target_date.isoformat() if target_date else None,
        "shiftId": None,
        "selectedShift": None,
        "options": [],
    }
    set_pending_update_shift_state(session, update_state)
    if not target_date:
        return "What day is the shift you want to update?"
    return None
