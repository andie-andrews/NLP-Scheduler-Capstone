import json
import re
from datetime import datetime, timedelta

from openai import OpenAI

from llm.openapi_loader import load_openapi_spec
from llm.openapi_parser import parse_operations
from llm.openapi_client import call_api
from llm.orchestration.intents import is_create_shift_intent, is_delete_shift_intent
from llm.orchestration.intents import is_update_shift_intent
from llm.orchestration.parsers import (
    extract_duration_hours,
    extract_schedule_name,
    extract_time_of_day,
    extract_week_range_from_message,
    extract_weekday_date,
    extract_weekday_datetime,
    find_name_in_message,
    format_shift_option_line,
    week_range_from_date,
)
from llm.orchestration.resolvers import (
    normalize_schedule_id_arg,
    resolve_employee_id,
    resolve_schedule_id,
)
from llm.orchestration.state_store import (
    clear_pending_employee_disambiguation_state,
    clear_pending_delete_shift_state,
    clear_pending_show_shifts_state,
    clear_pending_shift_state,
    clear_pending_update_shift_state,
    get_pending_employee_disambiguation_state,
    get_pending_delete_shift_state,
    get_pending_show_shifts_state,
    get_pending_shift_state,
    get_pending_update_shift_state,
    set_pending_employee_disambiguation_state,
    set_pending_show_shifts_state,
    set_pending_delete_shift_state,
    set_pending_shift_state,
    set_pending_update_shift_state,
)
from llm.orchestration.summary import summarize_shifts
from llm.orchestration.tools import build_tools, sanitize_tools_for_openai
from .prompts_v2 import SYSTEM_PROMPT, CALCULATION_RULES

client = OpenAI()

spec = load_openapi_spec()
OPERATIONS = parse_operations(spec)


def _build_create_shift_question(state):
    if not state.get("employeeId"):
        return "Sure — who should I schedule?"
    if not state.get("scheduleId"):
        return "Got it. Which schedule should I use?"
    if not state.get("start"):
        if state.get("pendingStartDate"):
            pending_date = datetime.fromisoformat(state["pendingStartDate"]).strftime("%A, %b %d")
            return f"What time should the shift start on {pending_date}?"
        return "What day/time should the shift start?"
    if not state.get("durationHours"):
        return "How long should the shift be (in hours)?"
    return None


def _next_missing_shift_field(state):
    if not state.get("employeeId"):
        return "employee"
    if not state.get("scheduleId"):
        return "schedule"
    if not state.get("start"):
        return "start"
    if not state.get("durationHours"):
        return "duration"
    return None


def _attempt_fill_shift_state_from_message(message, token, state):
    print("[create_shift][state] Filling state from message:", message)
    print("[create_shift][state] Before fill:", state)

    search_employees_op = OPERATIONS.get("searchEmployees")
    employees = call_api(token, search_employees_op, {"query": ""}) if search_employees_op else []

    name = find_name_in_message(message, employees) if employees else None
    if name and not state.get("employeeId"):
        resolution = resolve_employee_id(token, name, OPERATIONS, call_api)
        if resolution and resolution.get("type") == "resolved":
            state["employeeId"] = resolution["employeeId"]
        elif resolution and resolution.get("type") == "disambiguation":
            state["employee_options"] = resolution["raw"]
            state["awaiting"] = "employee_disambiguation"
            return {
                "type": "disambiguation",
                "entity": "employee",
                "options": resolution["options"],
            }

    duration = extract_duration_hours(message)
    if duration and not state.get("durationHours"):
        state["durationHours"] = duration

    if not state.get("start"):
        start = extract_weekday_datetime(message)
        if start:
            state["start"] = start
            state["pendingStartDate"] = None
        else:
            weekday_date = extract_weekday_date(message)
            if weekday_date:
                state["pendingStartDate"] = datetime.combine(weekday_date, datetime.min.time()).isoformat()

    if not state.get("start") and state.get("pendingStartDate"):
        parsed_time = extract_time_of_day(message)
        if parsed_time:
            pending_date = datetime.fromisoformat(state["pendingStartDate"]).date()
            start_dt = datetime.combine(pending_date, datetime.min.time()).replace(hour=parsed_time[0], minute=parsed_time[1])
            state["start"] = start_dt.isoformat()
            state["pendingStartDate"] = None

    if not state.get("scheduleId"):
        raw_message = message.strip()
        if raw_message.isdigit():
            state["scheduleId"] = int(raw_message)
            state["awaiting"] = None
            return None

        schedule_name = extract_schedule_name(message)
        if not schedule_name and state.get("awaiting") == "schedule":
            schedule_name = raw_message

        if schedule_name:
            schedule_resolution = resolve_schedule_id(token, schedule_name, OPERATIONS, call_api)
            if schedule_resolution and schedule_resolution.get("type") == "resolved":
                state["scheduleId"] = schedule_resolution["scheduleId"]
                state["awaiting"] = None
            elif schedule_resolution and schedule_resolution.get("type") == "disambiguation":
                state["schedule_options"] = schedule_resolution["raw"]
                state["awaiting"] = "schedule_disambiguation"
                return {
                    "type": "disambiguation",
                    "entity": "schedule",
                    "options": schedule_resolution["options"],
                }

    print("[create_shift][state] After fill:", state)
    return None


def _resolve_disambiguation_reply(message, state):
    choice_match = re.search(r"\b(\d+)\b", message)
    if not choice_match:
        return None

    choice = int(choice_match.group(1))
    awaiting = state.get("awaiting")
    if awaiting == "employee_disambiguation":
        options = state.get("employee_options", [])
        if 1 <= choice <= len(options):
            state["employeeId"] = options[choice - 1]["id"]
            state["awaiting"] = None
            return True
    if awaiting == "schedule_disambiguation":
        options = state.get("schedule_options", [])
        if 1 <= choice <= len(options):
            state["scheduleId"] = options[choice - 1]["id"]
            state["awaiting"] = None
            return True

    return False


def _resolve_employee_disambiguation_reply(message: str, options: list):
    choice_match = re.search(r"\b(\d+)\b", message or "")
    if choice_match:
        choice = int(choice_match.group(1))
        if 1 <= choice <= len(options):
            return options[choice - 1]
        return False

    normalized_reply = re.sub(r"\s+", " ", (message or "").strip().lower())
    if not normalized_reply:
        return None

    for option in options:
        first_name = (option.get("firstName") or "").strip()
        last_name = (option.get("lastName") or "").strip()
        full_name = f"{first_name} {last_name}".strip().lower()
        if normalized_reply == full_name:
            return option

    return None


def _build_employee_disambiguation_prompt(name: str, options: list):
    display_name = (name or "employee").strip() or "employee"
    option_lines = []
    for idx, option in enumerate(options, start=1):
        first_name = (option.get("firstName") or "").strip()
        last_name = (option.get("lastName") or "").strip()
        option_lines.append(f"{idx}. {first_name} {last_name}".strip())
    return (
        f"I found more than one {display_name}. Which employee do you want to see?\n\n"
        + "\n".join(option_lines)
    )


def _resolve_delete_shift_number_reply(message: str, state):
    choice_match = re.search(r"\b(\d+)\b", message)
    if not choice_match:
        return None
    choice = int(choice_match.group(1))
    options = state.get("options", [])
    if 1 <= choice <= len(options):
        return options[choice - 1]["id"]
    return False


def _resolve_shift_number_reply(message: str, state):
    choice_match = re.search(r"\b(\d+)\b", message)
    if not choice_match:
        return None
    choice = int(choice_match.group(1))
    options = state.get("options", [])
    if 1 <= choice <= len(options):
        return options[choice - 1]
    return False


def build_system_prompt(session: dict):
    role = session.get("role", "Employee")
    employee_id = session.get("employee_id", "UNKNOWN")
    memory = session.get("memory") if session else None
    last_employee_id = getattr(memory, "last_employee_id", None) if memory else None

    context = f"""
CURRENT USER CONTEXT:
- Role: {role}
- EmployeeId: {employee_id}
- LastReferencedEmployeeId: {last_employee_id if last_employee_id is not None else "NONE"}

RULES:
- If the user says "my", use employeeId = {employee_id}
- If the user is a Supervisor, they can query other employees
- If the user is an Employee, they can ONLY query their own data
- If the user asks a follow-up without naming an employee, reuse LastReferencedEmployeeId
"""

    tool_rules = """
TOOL USAGE RULES:
- You MUST call a function if one is available
- You MUST include ALL required parameters
- NEVER call a function with missing required parameters

Parameter rules:
- employeeId is REQUIRED for employee-related endpoints
- If a name is mentioned, resolve it to employeeId
- If employeeId is missing, DO NOT call the function

startDate/endDate:
- For "this week", use Sunday through Saturday
- For "next week", use next Sunday through next Saturday
- For "this month", use first day through last day of the current month
- If user does not provide a date range and you cannot infer one, ask a follow-up question

DO NOT return text if a function can be called.
ONLY return tool calls.
"""

    return SYSTEM_PROMPT + "\n\n" + context + "\n\n" + tool_rules + "\n\n" + CALCULATION_RULES


def run_orchestrator(message: str, token: str, session: dict):

    print("----- USER MESSAGE -----")
    print(message)
    lowered_message = (message or "").lower()

    pending_shift = get_pending_shift_state(session)
    pending_delete_shift = get_pending_delete_shift_state(session)
    pending_show_shifts = get_pending_show_shifts_state(session)
    pending_update_shift = get_pending_update_shift_state(session)
    pending_employee_disambiguation = get_pending_employee_disambiguation_state(session)

    if pending_employee_disambiguation:
        options = pending_employee_disambiguation.get("options", [])
        selected_employee = _resolve_employee_disambiguation_reply(message, options)
        if selected_employee is False:
            return _build_employee_disambiguation_prompt(
                pending_employee_disambiguation.get("name", "employee"),
                options,
            )
        if selected_employee:
            resolved_id = selected_employee.get("id")
            clear_pending_employee_disambiguation_state(session)
            follow_up_message = f"{pending_employee_disambiguation.get('original_message', '').strip()} (employeeId = {resolved_id})"
            return run_orchestrator(follow_up_message, token, session)
        return _build_employee_disambiguation_prompt(
            pending_employee_disambiguation.get("name", "employee"),
            options,
        )

    if pending_show_shifts:
        lower = (message or "").lower().strip()
        if re.search(r"\b(yes|yep|yeah|sure|show|ok|okay)\b", lower):
            clear_pending_show_shifts_state(session)
            lines = []
            for shift in pending_show_shifts.get("shifts", []):
                start = datetime.fromisoformat(shift["start"]).strftime("%A, %b %d at %I:%M %p")
                lines.append(f"- {start} for {shift.get('durationHours', 0)} hours")
            if not lines:
                return "You have no shifts in that range."
            return "Here are your shifts:\n" + "\n".join(lines)

        if re.search(r"\b(no|nope|nah|not now)\b", lower):
            clear_pending_show_shifts_state(session)
            return "No problem."

    if pending_shift and re.search(r"\b(start over|restart|cancel)\b", message.lower()):
        clear_pending_shift_state(session)
        pending_shift = None
        return "Okay — I cleared the in-progress shift. Tell me who and when you'd like to schedule."

    if pending_delete_shift and re.search(r"\b(start over|restart|cancel)\b", message.lower()):
        clear_pending_delete_shift_state(session)
        pending_delete_shift = None
        return "Okay — I cancelled the delete flow."

    if pending_update_shift and re.search(r"\b(start over|restart|cancel)\b", message.lower()):
        clear_pending_update_shift_state(session)
        pending_update_shift = None
        return "Okay — I cancelled the update flow."

    if pending_delete_shift:
        selected_shift_id = _resolve_delete_shift_number_reply(message, pending_delete_shift)
        if selected_shift_id is None:
            options = pending_delete_shift.get("options", [])
            option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(options)]
            return "Please reply with the shift number to delete:\n" + "\n".join(option_lines)
        if selected_shift_id is False:
            options = pending_delete_shift.get("options", [])
            option_lines = [format_shift_option_line(idx + 1, shift) for idx, shift in enumerate(options)]
            return "That number is out of range. Please choose one of these:\n" + "\n".join(option_lines)

        delete_result = call_api(token, OPERATIONS["deleteShift"], {"shiftId": selected_shift_id})
        clear_pending_delete_shift_state(session)
        return {
            "summary": f"Shift {selected_shift_id} deleted.",
            "data": {"deleteShiftResponse": delete_result, "deletedShiftId": selected_shift_id},
        }

    if is_delete_shift_intent(message):
        employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""})
        name = find_name_in_message(message, employees) if employees else None
        if not name:
            return "Who should I delete the shift for?"

        resolution = resolve_employee_id(token, name, OPERATIONS, call_api)
        if not resolution or resolution.get("type") == "not_found":
            return f"I couldn't find an employee matching '{name}'."
        if resolution.get("type") == "disambiguation":
            options = resolution["options"]
            option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(options)]
            return "I found multiple employees. Please choose one:\n" + "\n".join(option_lines)

        target_date = extract_weekday_date(message)
        if not target_date:
            return "What day should I delete the shift from?"

        week_start_date, week_end_date = week_range_from_date(datetime.combine(target_date, datetime.min.time()))
        shifts = call_api(
            token,
            OPERATIONS["getEmployeeShifts"],
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
            delete_result = call_api(token, OPERATIONS["deleteShift"], {"shiftId": shift_id})
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
                    OPERATIONS["getEmployeeShifts"],
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
                selected_shift = _resolve_shift_number_reply(message, pending_update_shift)
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

    if is_update_shift_intent(message):
        target_employee_id = session.get("employee_id")
        name = None
        if session.get("role") != "Employee":
            employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""})
            name = find_name_in_message(message, employees) if employees else None
            if name:
                resolution = resolve_employee_id(token, name, OPERATIONS, call_api)
                if not resolution or resolution.get("type") == "not_found":
                    return f"I couldn't find an employee matching '{name}'."
                if resolution.get("type") == "disambiguation":
                    options = resolution["options"]
                    option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(options)]
                    return "I found multiple employees. Please choose one:\n" + "\n".join(option_lines)
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

    if pending_shift and pending_shift.get("awaiting") in {"employee_disambiguation", "schedule_disambiguation"}:
        resolved = _resolve_disambiguation_reply(message, pending_shift)
        if resolved is None:
            pass
        elif resolved is False:
            options = pending_shift.get("employee_options") if pending_shift.get("awaiting") == "employee_disambiguation" else pending_shift.get("schedule_options")
            if not options:
                return "Please choose one of the listed options by number."
            lines = [f"{idx + 1}. {item.get('firstName', item.get('name', ''))} {item.get('lastName', '')}".strip() for idx, item in enumerate(options)]
            return "Please choose one option by number:\n" + "\n".join(lines)

    if pending_shift or is_create_shift_intent(message, OPERATIONS.get("createShift", {})):
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

        disambiguation = _attempt_fill_shift_state_from_message(message, token, state)
        if disambiguation:
            print("[create_shift] Disambiguation required:", disambiguation)
            options = disambiguation["options"]
            option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(options)]
            entity = disambiguation["entity"]
            return f"I found multiple {entity}s. Please choose one:\n" + "\n".join(option_lines)

        question = _build_create_shift_question(state)
        if question:
            print("[create_shift] Missing field, asking follow-up:", {"awaiting": _next_missing_shift_field(state), "question": question})
            state["awaiting"] = _next_missing_shift_field(state)
            set_pending_shift_state(session, state)
            return question

        args = {
            "scheduleId": state["scheduleId"],
            "employeeId": state["employeeId"],
            "start": state["start"],
            "durationHours": state["durationHours"],
        }
        normalized_schedule_id = normalize_schedule_id_arg(token, args.get("scheduleId"), OPERATIONS, call_api)
        if normalized_schedule_id is None:
            print("[create_shift] Schedule resolution failed for args:", args)
            state["scheduleId"] = None
            set_pending_shift_state(session, state)
            return "I couldn't match that schedule name. Which schedule should I use?"
        args["scheduleId"] = normalized_schedule_id
        print("[create_shift] Calling createShift with args:", args)
        result = call_api(token, OPERATIONS["createShift"], args)
        print("[create_shift] createShift response:", result)

        verification = None
        get_schedule_shifts = OPERATIONS.get("getScheduleShifts")
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

    memory = session.get("memory") if session else None
    last_employee_id = getattr(memory, "last_employee_id", None) if memory else None
    employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""})

    name = find_name_in_message(message, employees)
    effective_message = message

    if name:
        resolution = resolve_employee_id(token, name, OPERATIONS, call_api)

        if resolution["type"] == "not_found":
            return f"No employee found for '{name}'"

        if resolution["type"] == "disambiguation":
            set_pending_employee_disambiguation_state(
                session,
                {
                    "name": name,
                    "options": resolution["raw"],
                    "original_message": message,
                },
            )
            return _build_employee_disambiguation_prompt(name, resolution["raw"])

        if resolution["type"] == "resolved":
            employee_id = resolution["employeeId"]
            effective_message += f" (employeeId = {employee_id})"
            if memory and hasattr(memory, "save_last_employee"):
                memory.save_last_employee(employee_id)
            elif memory is not None:
                setattr(memory, "last_employee_id", employee_id)
            print(f"Resolved {name} → employeeId {employee_id}")
    elif (
        last_employee_id is not None
        and re.search(r"\b(week|month|shift|schedule|hours?)\b", lowered_message)
        and re.search(r"\b(next|this|what about|how many|scheduled|schedule)\b", lowered_message)
    ):
        effective_message += f" (employeeId = {last_employee_id})"
        print(f"Using last referenced employeeId {last_employee_id} for follow-up message.")

    tools = sanitize_tools_for_openai(build_tools(OPERATIONS))

    print("----- TOOLS -----")
    print([t["function"]["name"] for t in tools])

    system_prompt = build_system_prompt(session)

    print("----- SYSTEM PROMPT -----")
    print(system_prompt)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": effective_message}
        ],
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message

    if not msg.tool_calls:
        return "I couldn't determine what action to take. Try rephrasing."

    tool_call = msg.tool_calls[0]

    op_id = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")

    print("----- TOOL CALL -----")
    print(op_id)
    print(args)

    if op_id in {"getEmployeeShifts", "getScheduleShifts"}:
        if op_id == "getEmployeeShifts" and "employeeId" not in args and last_employee_id is not None:
            args["employeeId"] = last_employee_id

        inferred_range = extract_week_range_from_message(message)
        if inferred_range:
            # Force deterministic "this week"/"next week" ranges so model-generated
            # stale dates (e.g., old years) don't leak into API calls.
            args["startDate"] = inferred_range["startDate"]
            args["endDate"] = inferred_range["endDate"]
        elif (
            "next shift" in lowered_message
            or "next schedule" in lowered_message
            or "scheduled next" in lowered_message
        ):
            # If user asks for the next schedule/shift without an explicit range,
            # default to upcoming 30 days to avoid an unnecessary follow-up.
            today = datetime.now().date()
            args["startDate"] = today.isoformat()
            args["endDate"] = (today + timedelta(days=30)).isoformat()
        elif "startDate" not in args and "endDate" not in args:
            return "What date range should I use? I can use this week, next week, or this month."
    if op_id == "createShift":
        normalized_schedule_id = normalize_schedule_id_arg(token, args.get("scheduleId"), OPERATIONS, call_api)
        if normalized_schedule_id is None:
            return "I need a valid schedule. Please tell me the schedule name exactly, or provide its numeric scheduleId."
        args["scheduleId"] = normalized_schedule_id

    result = call_api(token, OPERATIONS[op_id], args)

    print("----- API RESULT -----")
    print(result)

    if op_id == "getEmployeeShifts":
        if memory is not None and args.get("employeeId") is not None:
            if hasattr(memory, "save_last_employee"):
                memory.save_last_employee(args["employeeId"])
            else:
                setattr(memory, "last_employee_id", args["employeeId"])
        employee_full_name = None
        target_employee_id = args.get("employeeId")
        if target_employee_id is not None and isinstance(employees, list):
            matched_employee = next(
                (emp for emp in employees if emp.get("id") == target_employee_id),
                None,
            )
            if matched_employee:
                first_name = (matched_employee.get("firstName") or "").strip()
                last_name = (matched_employee.get("lastName") or "").strip()
                employee_full_name = f"{first_name} {last_name}".strip() or None

        summary_data = summarize_shifts(result, message, employee_full_name=employee_full_name)
        lower_message = (message or "").lower()
        explicitly_asked_for_shifts = bool(
            re.search(r"\b(show|list|display)\b.*\bshift", lower_message)
            or re.search(r"\bwhat\b.*\bshifts?\b", lower_message)
            or re.search(r"\bmy shifts?\b", lower_message)
            or re.search(r"\bschedule\b", lower_message)
        )

        if summary_data.get("promptToShowShifts"):
            set_pending_show_shifts_state(
                session,
                {
                    "shifts": summary_data.get("shifts", []),
                    "totalHours": summary_data.get("totalHours", 0),
                },
            )
        else:
            clear_pending_show_shifts_state(session)

        response_data = dict(summary_data)
        if not explicitly_asked_for_shifts:
            response_data.pop("shifts", None)

        return {
            "summary": summary_data.get("summary", "No shifts found."),
            "data": response_data
        }

    return result
