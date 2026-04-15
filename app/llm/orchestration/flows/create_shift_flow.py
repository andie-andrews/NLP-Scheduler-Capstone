from datetime import datetime, timedelta


def _extract_error_detail(response_payload):
    if not isinstance(response_payload, dict):
        return None

    errors = response_payload.get("errors")
    if isinstance(errors, dict):
        if errors.get("overlapping_shift"):
            return errors["overlapping_shift"][0]

        for error_code, messages in errors.items():
            if isinstance(messages, list) and messages:
                return messages[0]
            if isinstance(messages, str) and messages:
                return messages
            if messages:
                return f"{error_code}: {messages}"

    if isinstance(errors, list):
        for item in errors:
            if isinstance(item, dict) and item.get("code") == "overlapping_shift" and item.get("message"):
                return item["message"]

        for item in errors:
            if isinstance(item, dict):
                message = item.get("message")
                if message:
                    return message
            elif isinstance(item, str) and item:
                return item

    raw_text = response_payload.get("rawText")
    if isinstance(raw_text, str) and raw_text.strip():
        first_line = raw_text.strip().splitlines()[0].strip()
        if first_line:
            return first_line

    return response_payload.get("title") or response_payload.get("detail") or response_payload.get("message")


def _format_shift_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def _format_shift_date(value: datetime) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def _build_single_shift_success_summary(state: dict, created_shift: dict) -> str:
    employee_name = _resolve_employee_label(state, created_shift)
    start_value = datetime.fromisoformat(created_shift["start"])
    end_value = start_value + timedelta(hours=created_shift["durationHours"])
    return (
        f"Shift created for {employee_name} on {_format_shift_date(start_value)} "
        f"from {_format_shift_time(start_value)} to {_format_shift_time(end_value)}."
    )


def _resolve_employee_label(state: dict, shift: dict) -> str:
    employee_name = (
        state.get("employeeName")
        or state.get("employeeDisplayName")
        or state.get("employee")
        or f"employee {shift.get('employeeId')}"
    )
    return employee_name


def _build_multi_shift_success_summary(state: dict, created_shifts: list[dict]) -> str:
    sorted_shifts = sorted(created_shifts, key=lambda shift: shift["start"])
    employee_name = _resolve_employee_label(state, sorted_shifts[0])
    starts = [datetime.fromisoformat(shift["start"]) for shift in sorted_shifts]
    first_start = starts[0]
    last_start = starts[-1]
    same_duration = len({shift["durationHours"] for shift in sorted_shifts}) == 1
    same_start_time = len({(start.hour, start.minute) for start in starts}) == 1
    same_weekday = len({start.weekday() for start in starts}) == 1

    if same_duration and same_start_time:
        end_time = _format_shift_time(first_start + timedelta(hours=sorted_shifts[0]["durationHours"]))
        if same_weekday and len(starts) > 1:
            day_name = first_start.strftime("%A")
            return (
                f"{len(sorted_shifts)} weekly shifts created for {employee_name} every {day_name} "
                f"from {_format_shift_time(first_start)} to {end_time} "
                f"({_format_shift_date(first_start)} to {_format_shift_date(last_start)})."
            )

        return (
            f"{len(sorted_shifts)} shifts created for {employee_name} "
            f"from {_format_shift_time(first_start)} to {end_time} "
            f"({_format_shift_date(first_start)} to {_format_shift_date(last_start)})."
        )

    return (
        f"{len(sorted_shifts)} shifts created for {employee_name} "
        f"between {_format_shift_date(first_start)} and {_format_shift_date(last_start)}."
    )


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
    **_unused,
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
        "multiShiftDates": [],
        "awaiting": None,
        "employee_options": [],
        "schedule_options": [],
    }
    set_pending_shift_state(session, state)

    disambiguation = attempt_fill_shift_state_from_message(message, token, state)
    if disambiguation:
        if disambiguation.get("type") == "reply":
            clear_pending_shift_state(session)
            return disambiguation.get("message")
        print("[create_shift] Disambiguation required:", disambiguation)
        options = disambiguation["options"]
        option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(options)]
        entity = disambiguation["entity"]
        return f"I found multiple {entity}s. Please choose one:\n" + "\n".join(option_lines)

    question = build_create_shift_question(state)
    recent_assignment = state.pop("recent_schedule_assignment", None)
    if question:
        if recent_assignment:
            employee_name = recent_assignment.get("employeeName") or "the employee"
            schedule_name = recent_assignment.get("scheduleName") or f"schedule {recent_assignment.get('scheduleId')}"
            question = f"Done — I added {employee_name} to {schedule_name}.\n\n{question}"
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

    recurring_dates = state.get("multiShiftDates") or []
    shifts_to_create = []
    if recurring_dates:
        base_start = datetime.fromisoformat(args["start"])
        for raw_date in recurring_dates:
            date_value = datetime.fromisoformat(raw_date).date()
            shifts_to_create.append({
                **args,
                "start": datetime.combine(date_value, base_start.time()).isoformat(),
            })
    else:
        shifts_to_create.append(args)

    get_schedule_shifts = operations.get("getScheduleShifts")
    should_skip_existing = len(shifts_to_create) > 1
    existing_matches_before = []
    if get_schedule_shifts and shifts_to_create and should_skip_existing:
        parsed_starts = [datetime.fromisoformat(shift["start"]) for shift in shifts_to_create]
        week_start_date, _ = week_range_from_date(min(parsed_starts))
        _, week_end_date = week_range_from_date(max(parsed_starts))
        existing_shifts = call_api(
            token,
            get_schedule_shifts,
            {
                "scheduleId": args["scheduleId"],
                "startDate": week_start_date.isoformat(),
                "endDate": week_end_date.isoformat(),
            },
        ) or []
        existing_matches_before = [
            s for s in existing_shifts
            if s.get("employeeId") == args["employeeId"]
            and any(
                s.get("start") == planned_shift["start"]
                and s.get("durationHours") == planned_shift["durationHours"]
                for planned_shift in shifts_to_create
            )
        ]
    else:
        week_start_date = None
        week_end_date = None

    if should_skip_existing:
        shifts_missing = []
        for shift_args in shifts_to_create:
            already_exists = any(
                existing.get("start") == shift_args["start"]
                and existing.get("durationHours") == shift_args["durationHours"]
                for existing in existing_matches_before
            )
            if not already_exists:
                shifts_missing.append(shift_args)
    else:
        shifts_missing = list(shifts_to_create)

    results = []
    successful_creates = []
    failed_creates = []
    for shift_args in shifts_missing:
        print("[create_shift] Calling createShift with args:", shift_args)
        created = call_api(token, operations["createShift"], shift_args)
        print("[create_shift] createShift response:", created)

        status_code = created.get("__httpStatus") if isinstance(created, dict) else None
        api_reported_failure = isinstance(created, dict) and created.get("success") is False
        status_reported_failure = status_code is not None and not (200 <= status_code < 300)
        if status_reported_failure or api_reported_failure:
            error_detail = _extract_error_detail(created)
            failed_creates.append({
                "shift": shift_args,
                "statusCode": status_code,
                "error": error_detail or "Validation failed.",
            })
        else:
            successful_creates.append(shift_args)

        results.append({"shift": shift_args, "response": created})

    verification = None
    if get_schedule_shifts:
        if week_start_date is None or week_end_date is None:
            parsed_starts = [datetime.fromisoformat(shift["start"]) for shift in shifts_to_create]
            week_start_date, _ = week_range_from_date(min(parsed_starts))
            _, week_end_date = week_range_from_date(max(parsed_starts))
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
            "expectedNewShiftCount": len(successful_creates),
            "matchingShiftCountBefore": len(existing_matches_before),
            "matchingShiftCount": len(
                [
                    s for s in (shifts or [])
                    if s.get("employeeId") == args["employeeId"]
                    and any(
                        s.get("start") == created_shift["start"]
                        and s.get("durationHours") == created_shift["durationHours"]
                        for created_shift in shifts_to_create
                    )
                ]
            ),
        }
        verification["matchingShiftCountAfter"] = verification["matchingShiftCount"]
        verification["createdCountInVerificationWindow"] = (
            verification["matchingShiftCountAfter"] - verification["matchingShiftCountBefore"]
        )
        print("[create_shift] Verification result:", verification)

    clear_pending_shift_state(session)
    if should_skip_existing and not shifts_missing:
        summary = "All requested shifts already exist on that schedule."
    elif failed_creates and successful_creates:
        if len(successful_creates) > 1:
            summary = (
                f"{_build_multi_shift_success_summary(state, successful_creates)} "
                f"{len(failed_creates)} additional shift(s) could not be created due to validation issues."
            )
        else:
            summary = (
                f"{_build_single_shift_success_summary(state, successful_creates[0])} "
                f"{len(failed_creates)} additional shift(s) could not be created due to validation issues."
            )
    elif failed_creates and not successful_creates:
        summary = "No shifts were created because all requested shifts failed validation."
    elif len(shifts_to_create) > 1:
        summary = _build_multi_shift_success_summary(state, successful_creates)
    else:
        summary = _build_single_shift_success_summary(state, successful_creates[0])

    return {
        "summary": summary,
        "data": {
            "createdCount": len(successful_creates),
            "failedCount": len(failed_creates),
            "failedShifts": failed_creates,
            "createShiftResponses": results,
            "createShiftResponse": results[0]["response"] if len(results) == 1 else None,
            "createdShift": args,
            "createdShifts": successful_creates,
            "requestedShifts": shifts_to_create,
            "skippedExistingShifts": [shift for shift in shifts_to_create if shift not in shifts_missing],
            "verification": verification,
        }
    }
