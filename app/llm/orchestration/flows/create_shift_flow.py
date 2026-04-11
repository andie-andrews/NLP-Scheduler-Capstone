from datetime import datetime


def handle_create_shift_flow(
    *,
    message: str,
    token: str,
    session: dict,
    pending_shift: dict | None,
    operations: dict,
    is_create_shift_intent,
    resolve_disambiguation_reply,
    attempt_fill_shift_state_from_message,
    build_create_shift_question,
    next_missing_shift_field,
    set_pending_shift_state,
    clear_pending_shift_state,
    normalize_schedule_id_arg,
    call_api,
    week_range_from_date,
):
    if pending_shift and pending_shift.get("awaiting") in {"employee_disambiguation", "schedule_disambiguation"}:
        resolved = resolve_disambiguation_reply(message, pending_shift)
        if resolved is None:
            pass
        elif resolved is False:
            options = pending_shift.get("employee_options") if pending_shift.get("awaiting") == "employee_disambiguation" else pending_shift.get("schedule_options")
            if not options:
                return "Please choose one of the listed options by number."
            lines = [f"{idx + 1}. {item.get('firstName', item.get('name', ''))} {item.get('lastName', '')}".strip() for idx, item in enumerate(options)]
            return "Please choose one option by number:\n" + "\n".join(lines)

    if not (pending_shift or is_create_shift_intent(message, operations.get("createShift", {}))):
        return None

    print("[create_shift] Entered create-shift flow.")
    state = pending_shift or {
        "intent": "create_shift",
        "employeeId": None,
        "scheduleId": None,
        "start": None,
        "pendingStartDate": None,
        "durationHours": None,
        "awaiting": None,
        "employee_options": [],
        "schedule_options": [],
    }
    set_pending_shift_state(session, state)

    disambiguation = attempt_fill_shift_state_from_message(message, token, state)
    if disambiguation:
        print("[create_shift] Disambiguation required:", disambiguation)
        options = disambiguation["options"]
        option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(options)]
        entity = disambiguation["entity"]
        return f"I found multiple {entity}s. Please choose one:\n" + "\n".join(option_lines)

    question = build_create_shift_question(state)
    if question:
        print("[create_shift] Missing field, asking follow-up:", {"awaiting": next_missing_shift_field(state), "question": question})
        state["awaiting"] = next_missing_shift_field(state)
        set_pending_shift_state(session, state)
        return question

    args = {
        "scheduleId": state["scheduleId"],
        "employeeId": state["employeeId"],
        "start": state["start"],
        "durationHours": state["durationHours"],
    }
    normalized_schedule_id = normalize_schedule_id_arg(token, args.get("scheduleId"), operations, call_api)
    if normalized_schedule_id is None:
        print("[create_shift] Schedule resolution failed for args:", args)
        state["scheduleId"] = None
        set_pending_shift_state(session, state)
        return "I couldn't match that schedule name. Which schedule should I use?"
    args["scheduleId"] = normalized_schedule_id
    print("[create_shift] Calling createShift with args:", args)
    result = call_api(token, operations["createShift"], args)
    print("[create_shift] createShift response:", result)

    verification = None
    get_schedule_shifts = operations.get("getScheduleShifts")
    if get_schedule_shifts:
        parsed_start = datetime.fromisoformat(args["start"])
        week_start_date, week_end_date = week_range_from_date(parsed_start)
        print(
            "[create_shift] Verifying created shift in schedule week:",
            {
                "scheduleId": args["scheduleId"],
                "startDate": week_start_date.isoformat(),
                "endDate": week_end_date.isoformat(),
            },
        )
        shifts = call_api(
            token,
            get_schedule_shifts,
            {
                "scheduleId": args["scheduleId"],
                "startDate": week_start_date.isoformat(),
                "endDate": week_end_date.isoformat(),
            },
        )
        verification = {
            "startDate": week_start_date.isoformat(),
            "endDate": week_end_date.isoformat(),
            "matchingShiftCount": len(
                [
                    s for s in (shifts or [])
                    if s.get("employeeId") == args["employeeId"]
                    and s.get("start") == args["start"]
                    and s.get("durationHours") == args["durationHours"]
                ]
            ),
        }
        print("[create_shift] Verification result:", verification)

    clear_pending_shift_state(session)
    return {
        "summary": "Shift created successfully.",
        "data": {
            "createShiftResponse": result,
            "createdShift": args,
            "verification": verification,
        }
    }
