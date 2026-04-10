import json
import re
from datetime import datetime, timedelta

from openai import OpenAI

from llm.openapi_loader import load_openapi_spec
from llm.openapi_parser import parse_operations
from llm.openapi_client import call_api
from llm.orchestration.intents import is_create_shift_intent, is_delete_shift_intent
from llm.orchestration.parsers import (
    extract_duration_hours,
    extract_schedule_name,
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
    clear_pending_delete_shift_state,
    clear_pending_show_shifts_state,
    clear_pending_shift_state,
    get_pending_delete_shift_state,
    get_pending_show_shifts_state,
    get_pending_shift_state,
    set_pending_show_shifts_state,
    set_pending_delete_shift_state,
    set_pending_shift_state,
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

    start = extract_weekday_datetime(message)
    if start and not state.get("start"):
        state["start"] = start

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


def _resolve_delete_shift_number_reply(message: str, state):
    choice_match = re.search(r"\b(\d+)\b", message)
    if not choice_match:
        return None
    choice = int(choice_match.group(1))
    options = state.get("options", [])
    if 1 <= choice <= len(options):
        return options[choice - 1]["id"]
    return False


def build_system_prompt(session: dict):
    role = session.get("role", "Employee")
    employee_id = session.get("employee_id", "UNKNOWN")

    context = f"""
CURRENT USER CONTEXT:
- Role: {role}
- EmployeeId: {employee_id}

RULES:
- If the user says "my", use employeeId = {employee_id}
- If the user is a Supervisor, they can query other employees
- If the user is an Employee, they can ONLY query their own data
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

    pending_shift = get_pending_shift_state(session)
    pending_delete_shift = get_pending_delete_shift_state(session)
    pending_show_shifts = get_pending_show_shifts_state(session)

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

    employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""})

    name = find_name_in_message(message, employees)

    if name:
        resolution = resolve_employee_id(token, name, OPERATIONS, call_api)

        if resolution["type"] == "not_found":
            return f"No employee found for '{name}'"

        if resolution["type"] == "disambiguation":
            return {
                "type": "disambiguation",
                "options": resolution["options"],
                "raw": resolution["raw"]
            }

        if resolution["type"] == "resolved":
            employee_id = resolution["employeeId"]
            message += f" (employeeId = {employee_id})"
            print(f"Resolved {name} → employeeId {employee_id}")

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
            {"role": "user", "content": message}
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
        inferred_range = extract_week_range_from_message(message)
        if inferred_range:
            # Force deterministic "this week"/"next week" ranges so model-generated
            # stale dates (e.g., old years) don't leak into API calls.
            args["startDate"] = inferred_range["startDate"]
            args["endDate"] = inferred_range["endDate"]
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
        summary_data = summarize_shifts(result, message)

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

        natural = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Explain results clearly to the user."},
                {"role": "user", "content": str(summary_data)}
            ]
        )

        return {
            "summary": natural.choices[0].message.content,
            "data": summary_data
        }

    return result
