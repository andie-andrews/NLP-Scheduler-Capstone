import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from llm.openapi_loader import load_openapi_spec
from llm.openapi_parser import parse_operations
from llm.openapi_client import call_api
from llm.orchestration.intents import (
    is_add_schedule_member_intent,
    is_create_employee_intent,
    is_create_schedule_intent,
    is_create_shift_intent,
    is_delete_employee_intent,
    is_delete_schedule_intent,
    is_delete_shift_intent,
    is_remove_schedule_member_intent,
    is_update_employee_intent,
    is_update_shift_intent,
)
from llm.orchestration.parsers import (
    extract_duration_hours,
    extract_recurring_shift_dates,
    extract_schedule_name,
    extract_time_of_day,
    extract_time_range,
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
    clear_pending_schedule_member_change_state,
    clear_pending_create_schedule_state,
    clear_pending_delete_schedule_state,
    clear_pending_employee_operation_state,
    get_pending_employee_disambiguation_state,
    get_pending_delete_shift_state,
    get_pending_show_shifts_state,
    get_pending_shift_state,
    get_pending_update_shift_state,
    get_pending_schedule_member_change_state,
    get_pending_create_schedule_state,
    get_pending_delete_schedule_state,
    get_pending_employee_operation_state,
    set_pending_employee_disambiguation_state,
    set_pending_show_shifts_state,
    set_pending_delete_shift_state,
    set_pending_shift_state,
    set_pending_update_shift_state,
    set_pending_schedule_member_change_state,
    set_pending_create_schedule_state,
    set_pending_delete_schedule_state,
    set_pending_employee_operation_state,
)
from llm.orchestration.summary import summarize_shifts
from llm.orchestration.tools import build_tools, sanitize_tools_for_openai
from llm.orchestration.context_resolution import (
    is_follow_up_employee_query,
    is_self_referential_employee_query,
)
from llm.orchestration.flow_context import (
    build_pending_flow_kwargs,
    build_shift_flow_kwargs,
)
from llm.orchestration.access_control import (
    ACCESS_GUARD_MESSAGE,
    is_supervisor,
    looks_like_other_employee_schedule_request,
)
from llm.orchestration.registry import FlowRegistry
from llm.orchestration.flows.create_shift_flow import handle_create_shift_flow
from llm.orchestration.flows.delete_shift_flow import handle_delete_shift_flow
from llm.orchestration.flows.update_shift_flow import handle_update_shift_flow
from llm.orchestration.flows.pending_schedule_flow import handle_pending_schedule_flow
from llm.orchestration.flows.pending_employee_flow import handle_pending_employee_flow
from .prompts_v2 import SYSTEM_PROMPT, CALCULATION_RULES

# Load environment variables for non-Streamlit entry points (e.g., assistant_api, tests, scripts).
APP_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = APP_DIR.parent
load_dotenv(APP_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

client = OpenAI()

spec = load_openapi_spec()
OPERATIONS = parse_operations(spec)


def _build_create_shift_question(state):
    if not state.get("employeeId"):
        return "Sure — who should I schedule?"
    if not state.get("scheduleId"):
        employee_schedule_options = state.get("employee_schedule_options") or []
        if employee_schedule_options:
            return (
                "Got it. Which schedule should I use? Here are this employee's schedules:\n"
                + _format_schedule_options(employee_schedule_options)
            )
        return (
            "I can't create a shift yet because this employee is not on any schedule. "
            "Please add the employee to a schedule in the Manage Schedules UI, then try again."
        )
    if not state.get("start"):
        if state.get("multiShiftDates"):
            return "What time should these shifts start?"
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


def _format_schedule_options(options: list):
    if not options:
        return ""

    lines = []
    for idx, schedule in enumerate(options):
        schedule_id = schedule.get("id")
        schedule_name = schedule.get("name") or f"Schedule {schedule_id}"
        lines.append(f"{idx + 1}. {schedule_name} (ID: {schedule_id})")
    return "\n".join(lines)


def _refresh_employee_schedule_state(token, state):
    employee_id = state.get("employeeId")
    if not employee_id:
        state["employee_schedule_options"] = []
        state["available_schedule_options"] = []
        return

    get_employee_schedules_op = OPERATIONS.get("getEmployeeSchedules")
    employee_schedules = []
    if get_employee_schedules_op:
        fetched_employee_schedules = call_api(token, get_employee_schedules_op, {"employeeId": employee_id}) or []
        if isinstance(fetched_employee_schedules, list):
            employee_schedules = fetched_employee_schedules

    state["employee_schedule_options"] = employee_schedules

    if employee_schedules:
        state["available_schedule_options"] = employee_schedules
        return

    get_schedules_op = OPERATIONS.get("getSchedules")
    all_schedules = call_api(token, get_schedules_op, {}) if get_schedules_op else []
    state["available_schedule_options"] = all_schedules if isinstance(all_schedules, list) else []


def _attempt_fill_shift_state_from_message(message, token, state):
    print("[create_shift][state] Filling state from message:", message)
    print("[create_shift][state] Before fill:", state)

    search_employees_op = OPERATIONS.get("searchEmployees")
    employees = call_api(token, search_employees_op, {"query": ""}) if search_employees_op else []

    disambiguation_payload = None

    name = find_name_in_message(message, employees) if employees else None
    if name and not state.get("employeeId"):
        resolution = resolve_employee_id(token, name, OPERATIONS, call_api)
        if resolution and resolution.get("type") == "resolved":
            state["employeeId"] = resolution["employeeId"]
            matched_employee = next(
                (employee for employee in employees if employee.get("id") == resolution["employeeId"]),
                None,
            )
            if matched_employee:
                first_name = (matched_employee.get("firstName") or "").strip()
                last_name = (matched_employee.get("lastName") or "").strip()
                state["employeeName"] = f"{first_name} {last_name}".strip() or None
            _refresh_employee_schedule_state(token, state)
        elif resolution and resolution.get("type") == "disambiguation":
            state["employee_options"] = resolution["raw"]
            state["awaiting"] = "employee_disambiguation"
            disambiguation_payload = {
                "type": "disambiguation",
                "entity": "employee",
                "options": resolution["options"],
            }

    duration = extract_duration_hours(message)
    if duration and not state.get("durationHours"):
        state["durationHours"] = duration

    recurring_dates = extract_recurring_shift_dates(message)
    if recurring_dates and not state.get("multiShiftDates"):
        state["multiShiftDates"] = [date.isoformat() for date in recurring_dates]

    time_range = extract_time_range(message)
    if time_range:
        if not state.get("durationHours"):
            state["durationHours"] = time_range["durationHours"]
        if not state.get("start"):
            if state.get("multiShiftDates"):
                first_date = datetime.fromisoformat(state["multiShiftDates"][0]).date()
                start_dt = datetime.combine(first_date, datetime.min.time()).replace(
                    hour=time_range["startHour"],
                    minute=time_range["startMinute"],
                )
                state["start"] = start_dt.isoformat()
            else:
                parsed_date = extract_weekday_date(message)
                if parsed_date:
                    start_dt = datetime.combine(parsed_date, datetime.min.time()).replace(
                        hour=time_range["startHour"],
                        minute=time_range["startMinute"],
                    )
                    state["start"] = start_dt.isoformat()

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

    if not state.get("start") and state.get("multiShiftDates"):
        parsed_time = extract_time_of_day(message)
        if parsed_time:
            first_date = datetime.fromisoformat(state["multiShiftDates"][0]).date()
            state["start"] = datetime.combine(first_date, datetime.min.time()).replace(
                hour=parsed_time[0],
                minute=parsed_time[1],
            ).isoformat()

    if state.get("employeeId") and "employee_schedule_options" not in state:
        _refresh_employee_schedule_state(token, state)

    employee_schedule_options = state.get("employee_schedule_options") or []
    if not state.get("scheduleId") and len(employee_schedule_options) == 1:
        state["scheduleId"] = employee_schedule_options[0]["id"]
        state["awaiting"] = None

    if not state.get("scheduleId"):
        raw_message = message.strip()
        if raw_message.isdigit() and employee_schedule_options:
            choice = int(raw_message)
            if 1 <= choice <= len(employee_schedule_options):
                state["scheduleId"] = employee_schedule_options[choice - 1]["id"]
                state["awaiting"] = None
                return None
            matching_schedule = next(
                (schedule for schedule in employee_schedule_options if schedule.get("id") == choice),
                None,
            )
            if matching_schedule:
                state["scheduleId"] = matching_schedule["id"]
                state["awaiting"] = None
                return None

        schedule_name = extract_schedule_name(message)
        if not schedule_name and state.get("awaiting") == "schedule":
            schedule_name = raw_message

        if schedule_name:
            schedule_resolution = resolve_schedule_id(token, schedule_name, OPERATIONS, call_api)
            if schedule_resolution and schedule_resolution.get("type") == "resolved":
                resolved_schedule_id = schedule_resolution["scheduleId"]
                if employee_schedule_options and resolved_schedule_id not in {
                    s.get("id") for s in employee_schedule_options
                }:
                    state["awaiting"] = "schedule"
                else:
                    state["scheduleId"] = resolved_schedule_id
                    state["awaiting"] = None
            elif schedule_resolution and schedule_resolution.get("type") == "disambiguation":
                scoped_options = schedule_resolution["raw"]
                if employee_schedule_options:
                    allowed_ids = {s.get("id") for s in employee_schedule_options}
                    scoped_options = [s for s in scoped_options if s.get("id") in allowed_ids]

                if scoped_options:
                    state["schedule_options"] = scoped_options
                    state["awaiting"] = "schedule_disambiguation"
                    disambiguation_payload = {
                        "type": "disambiguation",
                        "entity": "schedule",
                        "options": [
                            f"{s.get('name')} (ID: {s.get('id')})"
                            for s in scoped_options
                        ],
                    }
                else:
                    state["awaiting"] = "schedule"

    print("[create_shift][state] After fill:", state)
    return disambiguation_payload


def _resolve_disambiguation_reply(message, state):
    awaiting = state.get("awaiting")
    if awaiting == "employee_disambiguation":
        options = state.get("employee_options", [])
        selected = _resolve_employee_disambiguation_reply(message, options)
        if selected is False:
            return False
        if selected:
            state["employeeId"] = selected["id"]
            first_name = (selected.get("firstName") or "").strip()
            last_name = (selected.get("lastName") or "").strip()
            state["employeeName"] = f"{first_name} {last_name}".strip() or None
            state["awaiting"] = None
            return True
        return None

    choice_match = re.search(r"\b(\d+)\b", message)
    if not choice_match:
        return None

    choice = int(choice_match.group(1))
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


def _extract_explicit_employee_id(message: str):
    match = re.search(r"employeeid\s*=\s*(\d+)", message or "", flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _get_employee_directory(token: str, operations: dict, api_caller, memory):
    cached = getattr(memory, "employee_directory", None) if memory else None
    if isinstance(cached, list) and cached:
        return cached

    search_op = operations.get("searchEmployees")
    if not search_op:
        return []

    employees = api_caller(token, search_op, {"query": ""}) or []
    if memory and hasattr(memory, "save_employee_directory"):
        memory.save_employee_directory(employees)
    elif memory is not None:
        setattr(memory, "employee_directory", employees)
    return employees


def _resolve_employee_from_directory(name: str, employees: list):
    normalized = (name or "").strip().lower()
    if not normalized or not isinstance(employees, list):
        return None

    exact_full_matches = []
    exact_first_matches = []
    partial_matches = []

    for emp in employees:
        first_name = (emp.get("firstName") or "").strip().lower()
        last_name = (emp.get("lastName") or "").strip().lower()
        full_name = f"{first_name} {last_name}".strip()

        if normalized == full_name and full_name:
            exact_full_matches.append(emp)
        elif normalized == first_name and first_name:
            exact_first_matches.append(emp)
        elif normalized in full_name and full_name:
            partial_matches.append(emp)

    matches = exact_full_matches or exact_first_matches or partial_matches
    if not matches:
        return {"type": "not_found"}
    if len(matches) == 1:
        return {"type": "resolved", "employeeId": matches[0]["id"]}
    return {"type": "disambiguation", "raw": matches}


def _extract_employee_name_parts(message: str):
    text = (message or "").strip()
    quoted = re.search(r"['\"]([^'\"]+)['\"]", text)
    candidate = quoted.group(1).strip() if quoted else text

    generic_phrases = {
        "employee",
        "an employee",
        "a employee",
        "new employee",
        "add employee",
        "add an employee",
        "create employee",
        "create an employee",
    }
    if candidate.lower().strip(" .?!") in generic_phrases:
        return None, None

    patterns = [
        r"(?:employee\s+)?named\s+([a-zA-Z]+)\s+([a-zA-Z]+)",
        r"(?:employee\s+)?name\s+is\s+([a-zA-Z]+)\s+([a-zA-Z]+)",
        r"(?:add|create|new|hire|update|edit|change)\s+(?:employee\s+)?([a-zA-Z]+)\s+([a-zA-Z]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, candidate, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().title(), match.group(2).strip().title()

    ignored = {
        "employee", "add", "create", "new", "hire", "update", "edit", "change", "delete", "remove",
        "can", "you", "please", "an", "a", "the", "me",
    }
    tokens = [token for token in re.findall(r"[a-zA-Z]+", candidate) if token.lower() not in ignored]
    if len(tokens) >= 2:
        if tokens[-2].lower() in {"an", "a", "employee"} or tokens[-1].lower() == "employee":
            return None, None
        return tokens[-2].title(), tokens[-1].title()
    return None, None


def _extract_role_id(message: str):
    text = (message or "").lower()
    explicit = re.search(r"role\s*id\s*[:=]?\s*(\d+)", text)
    if explicit:
        return int(explicit.group(1))
    if "supervisor" in text or "manager" in text:
        return 2
    if re.search(r"\b(as|role)\s+(an?\s+)?employee\b", text):
        return 1
    return None


def _extract_schedule_name_for_create(message: str):
    text = (message or "").strip()
    quoted = re.search(r"['\"]([^'\"]+)['\"]", text)
    if quoted:
        return quoted.group(1).strip()

    patterns = [
        r"(?:create|new|make|add)\s+(?:a\s+)?schedule(?:\s+(?:called|named))?\s+([a-zA-Z0-9 _'’-]+)$",
        r"schedule(?:\s+(?:called|named))?\s+([a-zA-Z0-9 _'’-]+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,!?:;\"'")
            if candidate:
                return candidate
    return None


def _extract_schedule_name_or_id_from_message(message: str):
    def normalize_schedule_candidate(value: str | None):
        if not value:
            return None
        cleaned = value.strip(" .,!?:;\"'")
        cleaned = re.sub(r"^(the|a|an)\s+", "", cleaned, flags=re.IGNORECASE).strip()
        if cleaned.lower() in {"", "schedule", "my"}:
            return None
        return cleaned

    raw = (message or "").strip()
    if raw.isdigit():
        return int(raw)

    id_match = re.search(r"schedule\s*id\s*[:=]?\s*(\d+)", raw, flags=re.IGNORECASE)
    if id_match:
        return int(id_match.group(1))

    name = extract_schedule_name(raw)
    if name:
        normalized = name.strip().lower()
        if normalized in {"a", "an", "the", "my"}:
            return None
        return normalize_schedule_candidate(name)

    to_schedule_match = re.search(r"\bto\s+(?:the\s+|a\s+|an\s+)?([a-zA-Z0-9 _'’-]+?)\s+schedule\b", raw, flags=re.IGNORECASE)
    if to_schedule_match:
        candidate = normalize_schedule_candidate(to_schedule_match.group(1))
        if candidate:
            return candidate

    from_schedule_match = re.search(r"\bfrom\s+(?:the\s+|a\s+|an\s+)?([a-zA-Z0-9 _'’-]+?)\s+schedule\b", raw, flags=re.IGNORECASE)
    if from_schedule_match:
        candidate = normalize_schedule_candidate(from_schedule_match.group(1))
        if candidate:
            return candidate

    return None


def _extract_member_role_target(message: str):
    text = (message or "").lower()
    if "manager" in text or "supervisor" in text:
        return "manager"
    return "employee"


def _get_schedule_member_operation(action: str):
    return OPERATIONS.get("addEmployeeToSchedule") if action == "add" else OPERATIONS.get("removeEmployeeFromSchedule")


def _is_affirmative(message: str):
    return bool(re.search(r"\b(yes|yep|yeah|sure|ok|okay|please do|create it)\b", (message or "").lower()))


def _is_negative(message: str):
    return bool(re.search(r"\b(no|nope|nah|don't|do not|not now)\b", (message or "").lower()))


def _extract_schedule_change_target_name(message: str, employees: list):
    text = (message or "").lower()
    patterns = [
        r"(?:add|assign|include|put)\s+(.+?)\s+to\s+.+schedule",
        r"(?:remove|unassign|delete|take off)\s+(.+?)\s+(?:from|off)\s+.+schedule",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        candidate = re.sub(r"\s+", " ", match.group(1).strip())
        for emp in employees or []:
            full_name = f"{(emp.get('firstName') or '').strip()} {(emp.get('lastName') or '').strip()}".strip().lower()
            if full_name and (candidate == full_name or full_name in candidate):
                return full_name
    return None


def _build_schedule_member_schedule_question(state: dict):
    action = "add" if state.get("action") == "add" else "remove"
    employee_name = state.get("employeeName")
    if employee_name:
        return f"Sure — what schedule did you want to {action} {employee_name} {'to' if action == 'add' else 'from'}?"
    return "Which schedule should I update?"


def _lookup_schedule_name_by_id(token: str, schedule_id: int | None):
    if not schedule_id:
        return None
    get_schedules_op = OPERATIONS.get("getSchedules")
    if not get_schedules_op:
        return None
    schedules = call_api(token, get_schedules_op, {}) or []
    match = next((s for s in schedules if s.get("id") == schedule_id), None)
    return (match or {}).get("name")


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
    explicit_employee_id = _extract_explicit_employee_id(message)

    pending_shift = get_pending_shift_state(session)
    pending_delete_shift = get_pending_delete_shift_state(session)
    pending_show_shifts = get_pending_show_shifts_state(session)
    pending_update_shift = get_pending_update_shift_state(session)
    pending_employee_disambiguation = get_pending_employee_disambiguation_state(session)
    pending_schedule_member_change = get_pending_schedule_member_change_state(session)
    pending_create_schedule = get_pending_create_schedule_state(session)
    pending_delete_schedule = get_pending_delete_schedule_state(session)
    pending_employee_operation = get_pending_employee_operation_state(session)

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

    if pending_schedule_member_change and re.search(r"\b(start over|restart|cancel)\b", message.lower()):
        clear_pending_schedule_member_change_state(session)
        pending_schedule_member_change = None
        return "Okay — I cancelled the schedule member update flow."

    if pending_create_schedule and re.search(r"\b(start over|restart|cancel)\b", message.lower()):
        clear_pending_create_schedule_state(session)
        pending_create_schedule = None
        return "Okay — I cancelled creating a new schedule."

    if pending_delete_schedule and re.search(r"\b(start over|restart|cancel)\b", message.lower()):
        clear_pending_delete_schedule_state(session)
        pending_delete_schedule = None
        return "Okay — I cancelled deleting the schedule."

    if pending_employee_operation and re.search(r"\b(start over|restart|cancel)\b", message.lower()):
        clear_pending_employee_operation_state(session)
        pending_employee_operation = None
        return "Okay — I cancelled the employee update flow."

    pending_flow_registry = FlowRegistry()
    pending_flow_registry.register("pending_schedule", handle_pending_schedule_flow)
    pending_flow_registry.register("pending_employee", handle_pending_employee_flow)
    pending_flow_result = pending_flow_registry.dispatch(**build_pending_flow_kwargs(
        message=message,
        token=token,
        session=session,
        pending_create_schedule=pending_create_schedule,
        pending_delete_schedule=pending_delete_schedule,
        pending_employee_operation=pending_employee_operation,
        operations=OPERATIONS,
        call_api=call_api,
        clear_pending_create_schedule_state=clear_pending_create_schedule_state,
        clear_pending_delete_schedule_state=clear_pending_delete_schedule_state,
        extract_schedule_name_or_id_from_message=_extract_schedule_name_or_id_from_message,
        normalize_schedule_id_arg=normalize_schedule_id_arg,
        lookup_schedule_name_by_id=_lookup_schedule_name_by_id,
        extract_employee_name_parts=_extract_employee_name_parts,
        extract_role_id=_extract_role_id,
        extract_explicit_employee_id=_extract_explicit_employee_id,
        resolve_employee_id=resolve_employee_id,
        set_pending_employee_operation_state=set_pending_employee_operation_state,
        clear_pending_employee_operation_state=clear_pending_employee_operation_state,
    ))
    if pending_flow_result is not None:
        return pending_flow_result

    if pending_schedule_member_change:
        if pending_schedule_member_change.get("awaitingCreateSchedule"):
            pending_schedule_member_change["awaitingCreateSchedule"] = False
            pending_schedule_member_change["suggestedScheduleName"] = None
            set_pending_schedule_member_change_state(session, pending_schedule_member_change)
            return (
                "I can't create schedules from chat. Please create the schedule in the Manage Schedules UI, "
                "then tell me the schedule name."
            )

        if not pending_schedule_member_change.get("employeeId"):
            choice = re.search(r"\b(\d+)\b", message or "")
            option_employees = pending_schedule_member_change.get("employeeOptions") or []
            if choice and option_employees:
                idx = int(choice.group(1))
                if 1 <= idx <= len(option_employees):
                    chosen = option_employees[idx - 1]
                    pending_schedule_member_change["employeeId"] = chosen["id"]
                    pending_schedule_member_change["employeeName"] = (
                        f"{(chosen.get('firstName') or '').strip()} {(chosen.get('lastName') or '').strip()}".strip()
                    )
                    pending_schedule_member_change["employeeOptions"] = []
                else:
                    option_lines = [
                        f"{index + 1}. {item.get('firstName', '').strip()} {item.get('lastName', '').strip()}".strip()
                        for index, item in enumerate(option_employees)
                    ]
                    return "That number is out of range. Please choose one:\n" + "\n".join(option_lines)
            else:
                employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""}) or []
                name = find_name_in_message(message, employees) if employees else None
                if not name:
                    return "Which employee should I use?"
                resolution = resolve_employee_id(token, name, OPERATIONS, call_api)
                if not resolution or resolution.get("type") == "not_found":
                    return f"I couldn't find an employee matching '{name}'."
                if resolution.get("type") == "disambiguation":
                    pending_schedule_member_change["employeeOptions"] = resolution["raw"]
                    option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(resolution["options"])]
                    set_pending_schedule_member_change_state(session, pending_schedule_member_change)
                    return "I found multiple employees. Please choose one:\n" + "\n".join(option_lines)
                pending_schedule_member_change["employeeId"] = resolution["employeeId"]
                matched = next((emp for emp in employees if emp.get("id") == resolution["employeeId"]), None)
                if matched:
                    pending_schedule_member_change["employeeName"] = (
                        f"{(matched.get('firstName') or '').strip()} {(matched.get('lastName') or '').strip()}".strip()
                    )

        if not pending_schedule_member_change.get("scheduleId"):
            schedule_target = _extract_schedule_name_or_id_from_message(message)
            resolved_schedule_id = normalize_schedule_id_arg(token, schedule_target, OPERATIONS, call_api)
            if resolved_schedule_id is None:
                set_pending_schedule_member_change_state(session, pending_schedule_member_change)
                if isinstance(schedule_target, str):
                    return (
                        f"I couldn't find schedule '{schedule_target}'. "
                        "Please create it in the Manage Schedules UI or choose an existing schedule."
                    )
                return _build_schedule_member_schedule_question(pending_schedule_member_change)
            pending_schedule_member_change["scheduleId"] = resolved_schedule_id
            if isinstance(schedule_target, str):
                pending_schedule_member_change["scheduleName"] = schedule_target

        operation = _get_schedule_member_operation(pending_schedule_member_change.get("action"))
        if not operation:
            clear_pending_schedule_member_change_state(session)
            return "Schedule member update is not available because the API spec is missing that operation."
        call_api(
            token,
            operation,
            {
                "scheduleId": pending_schedule_member_change["scheduleId"],
                "employeeId": pending_schedule_member_change["employeeId"],
            },
        )
        action_word = "added to" if pending_schedule_member_change.get("action") == "add" else "removed from"
        role_word = pending_schedule_member_change.get("roleTarget", "employee")
        employee_display = pending_schedule_member_change.get("employeeName") or f"{role_word} {pending_schedule_member_change['employeeId']}"
        schedule_display = (
            pending_schedule_member_change.get("scheduleName")
            or _lookup_schedule_name_by_id(token, pending_schedule_member_change.get("scheduleId"))
            or f"schedule {pending_schedule_member_change['scheduleId']}"
        )
        clear_pending_schedule_member_change_state(session)
        return f"Done — {employee_display} was {action_word} {schedule_display}."

    if is_create_schedule_intent(message):
        clear_pending_create_schedule_state(session)
        return "Schedule creation is only available in the Manage Schedules UI."

    if is_delete_schedule_intent(message):
        schedule_target = _extract_schedule_name_or_id_from_message(message)
        if not schedule_target:
            set_pending_delete_schedule_state(session, {"intent": "delete_schedule"})
            return "Which schedule do you want me to delete?"
        resolved_schedule_id = normalize_schedule_id_arg(token, schedule_target, OPERATIONS, call_api)
        if resolved_schedule_id is None:
            set_pending_delete_schedule_state(session, {"intent": "delete_schedule"})
            return "I couldn't find that schedule. Which schedule do you want me to delete?"
        delete_operation = OPERATIONS.get("deleteSchedule")
        if not delete_operation:
            return "Deleting schedules is not available because the API spec is missing deleteSchedule."
        call_api(token, delete_operation, {"scheduleId": resolved_schedule_id})
        schedule_name = schedule_target if isinstance(schedule_target, str) else _lookup_schedule_name_by_id(token, resolved_schedule_id)
        return f"Done — deleted schedule {schedule_name or resolved_schedule_id}."

    if is_create_employee_intent(message):
        first_name, last_name = _extract_employee_name_parts(message)
        role_id = _extract_role_id(message)
        state = {
            "action": "create",
            "firstName": first_name,
            "lastName": last_name,
            "roleId": role_id,
        }
        set_pending_employee_operation_state(session, state)
        if not first_name or not last_name or role_id is None:
            missing = []
            if not first_name:
                missing.append("first name")
            if not last_name:
                missing.append("last name")
            if role_id is None:
                missing.append("role (employee or supervisor)")
            return "I can add that employee. Please provide: " + ", ".join(missing) + "."
        created = call_api(token, OPERATIONS["createEmployee"], {"firstName": first_name, "lastName": last_name, "roleId": role_id})
        clear_pending_employee_operation_state(session)
        created_id = created.get("id")
        return f"Done — created employee {first_name} {last_name}" + (f" (ID: {created_id})." if created_id is not None else ".")

    if is_update_employee_intent(message):
        first_name, last_name = _extract_employee_name_parts(message)
        role_id = _extract_role_id(message)
        state = {
            "action": "update",
            "employeeId": _extract_explicit_employee_id(message),
            "firstName": first_name,
            "lastName": last_name,
            "roleId": role_id,
            "employeeOptions": [],
        }
        set_pending_employee_operation_state(session, state)
        return run_orchestrator("", token, session)

    if is_delete_employee_intent(message):
        first_name, last_name = _extract_employee_name_parts(message)
        state = {
            "action": "delete",
            "employeeId": _extract_explicit_employee_id(message),
            "firstName": first_name,
            "lastName": last_name,
            "employeeOptions": [],
        }
        set_pending_employee_operation_state(session, state)
        return run_orchestrator("", token, session)

    if is_add_schedule_member_intent(message) or is_remove_schedule_member_intent(message):
        employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""}) or []
        action = "add" if is_add_schedule_member_intent(message) else "remove"
        role_target = _extract_member_role_target(message)
        name = _extract_schedule_change_target_name(message, employees) or (
            find_name_in_message(message, employees) if employees else None
        )
        state = {
            "action": action,
            "roleTarget": role_target,
            "employeeId": None,
            "employeeName": None,
            "scheduleId": None,
            "scheduleName": None,
            "employeeOptions": [],
            "awaitingCreateSchedule": False,
            "suggestedScheduleName": None,
        }
        if name:
            resolution = resolve_employee_id(token, name, OPERATIONS, call_api)
            if resolution and resolution.get("type") == "resolved":
                state["employeeId"] = resolution["employeeId"]
                matched = next((emp for emp in employees if emp.get("id") == state["employeeId"]), None)
                if matched:
                    state["employeeName"] = f"{(matched.get('firstName') or '').strip()} {(matched.get('lastName') or '').strip()}".strip()
            elif resolution and resolution.get("type") == "disambiguation":
                state["employeeOptions"] = resolution["raw"]
                set_pending_schedule_member_change_state(session, state)
                option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(resolution["options"])]
                return "I found multiple employees. Please choose one:\n" + "\n".join(option_lines)
            elif resolution and resolution.get("type") == "not_found":
                return f"I couldn't find an employee matching '{name}'."

        if state["employeeId"] is not None and role_target == "manager":
            employee = next((emp for emp in employees if emp.get("id") == state["employeeId"]), None)
            if employee and employee.get("roleId") != 2:
                return "That employee is not a manager/supervisor. Please choose someone with supervisor role."

        raw_schedule_target = _extract_schedule_name_or_id_from_message(message)
        if raw_schedule_target:
            state["scheduleId"] = normalize_schedule_id_arg(token, raw_schedule_target, OPERATIONS, call_api)
            if isinstance(raw_schedule_target, str):
                state["scheduleName"] = raw_schedule_target

        if state["employeeId"] is None or state["scheduleId"] is None:
            set_pending_schedule_member_change_state(session, state)
            if state["employeeId"] is None:
                return "Who should I update on the schedule?"
            if isinstance(raw_schedule_target, str):
                return (
                    f"I couldn't find schedule '{raw_schedule_target}'. "
                    "Please create it in the Manage Schedules UI or choose an existing schedule."
                )
            return _build_schedule_member_schedule_question(state)

        operation = _get_schedule_member_operation(action)
        if not operation:
            return "Schedule member update is not available because the API spec is missing that operation."
        call_api(token, operation, {"scheduleId": state["scheduleId"], "employeeId": state["employeeId"]})
        action_word = "added to" if action == "add" else "removed from"
        employee_display = state.get("employeeName") or f"{role_target} {state['employeeId']}"
        schedule_display = (
            state.get("scheduleName")
            or _lookup_schedule_name_by_id(token, state.get("scheduleId"))
            or f"schedule {state['scheduleId']}"
        )
        return f"Done — {employee_display} was {action_word} {schedule_display}."

    flow_registry = FlowRegistry()
    flow_registry.register("delete_shift", handle_delete_shift_flow)
    flow_registry.register("update_shift", handle_update_shift_flow)
    flow_registry.register("create_shift", handle_create_shift_flow)
    flow_result = flow_registry.dispatch(**build_shift_flow_kwargs(
        message=message,
        token=token,
        session=session,
        pending_shift=pending_shift,
        pending_delete_shift=pending_delete_shift,
        pending_update_shift=pending_update_shift,
        explicit_employee_id=explicit_employee_id,
        operations=OPERATIONS,
        is_create_shift_intent=is_create_shift_intent,
        is_delete_shift_intent=is_delete_shift_intent,
        is_update_shift_intent=is_update_shift_intent,
        find_name_in_message=find_name_in_message,
        resolve_employee_id=resolve_employee_id,
        set_pending_employee_disambiguation_state=set_pending_employee_disambiguation_state,
        build_employee_disambiguation_prompt=_build_employee_disambiguation_prompt,
        extract_weekday_date=extract_weekday_date,
        resolve_disambiguation_reply=_resolve_disambiguation_reply,
        attempt_fill_shift_state_from_message=_attempt_fill_shift_state_from_message,
        build_create_shift_question=_build_create_shift_question,
        next_missing_shift_field=_next_missing_shift_field,
        format_shift_option_line=format_shift_option_line,
        resolve_delete_shift_number_reply=_resolve_delete_shift_number_reply,
        resolve_shift_number_reply=_resolve_shift_number_reply,
        extract_time_of_day=extract_time_of_day,
        extract_duration_hours=extract_duration_hours,
        clear_pending_delete_shift_state=clear_pending_delete_shift_state,
        set_pending_delete_shift_state=set_pending_delete_shift_state,
        clear_pending_update_shift_state=clear_pending_update_shift_state,
        set_pending_update_shift_state=set_pending_update_shift_state,
        set_pending_shift_state=set_pending_shift_state,
        clear_pending_shift_state=clear_pending_shift_state,
        normalize_schedule_id_arg=normalize_schedule_id_arg,
        call_api=call_api,
        week_range_from_date=week_range_from_date,
    ))
    if flow_result is not None:
        return flow_result

    memory = session.get("memory") if session else None
    has_supervisor_access = is_supervisor(session)
    current_employee_id = session.get("employee_id") if session else None
    last_employee_id = getattr(memory, "last_employee_id", None) if memory else None
    employees = _get_employee_directory(token, OPERATIONS, call_api, memory)
    name = find_name_in_message(message, employees) if employees else None
    effective_message = message

    if (
        not has_supervisor_access
        and looks_like_other_employee_schedule_request(message, current_employee_id)
        and not is_self_referential_employee_query(lowered_message)
    ):
        return ACCESS_GUARD_MESSAGE

    if explicit_employee_id is not None:
        if not has_supervisor_access and current_employee_id is not None and explicit_employee_id != current_employee_id:
            return ACCESS_GUARD_MESSAGE
        effective_message += f" (employeeId = {explicit_employee_id})"
        if memory and hasattr(memory, "save_last_employee"):
            memory.save_last_employee(explicit_employee_id)
        elif memory is not None:
            setattr(memory, "last_employee_id", explicit_employee_id)
    elif name:
        local_resolution = _resolve_employee_from_directory(name, employees)
        if local_resolution and local_resolution.get("type") == "resolved":
            resolution = local_resolution
        elif local_resolution and local_resolution.get("type") == "disambiguation":
            resolution = {
                "type": "disambiguation",
                "raw": local_resolution["raw"],
            }
        else:
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
            if not has_supervisor_access and current_employee_id is not None and employee_id != current_employee_id:
                return ACCESS_GUARD_MESSAGE
            effective_message += f" (employeeId = {employee_id})"
            if memory and hasattr(memory, "save_last_employee"):
                memory.save_last_employee(employee_id)
            elif memory is not None:
                setattr(memory, "last_employee_id", employee_id)
            print(f"Resolved {name} → employeeId {employee_id}")
    elif (
        session.get("employee_id") is not None
        and is_self_referential_employee_query(lowered_message)
    ):
        effective_message += f" (employeeId = {session['employee_id']})"
        if memory and hasattr(memory, "save_last_employee"):
            memory.save_last_employee(session["employee_id"])
        elif memory is not None:
            setattr(memory, "last_employee_id", session["employee_id"])
        print(f"Using session employee_id {session['employee_id']} for self-referential request.")
    elif (
        last_employee_id is not None
        and is_follow_up_employee_query(lowered_message)
        and not is_self_referential_employee_query(lowered_message)
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
        if re.search(r"\b(hours?|work|worked|schedule|shift)\b", lowered_message):
            return "What date range should I use? I can use this week, next week, or this month."
        return "I couldn't determine what action to take. Try rephrasing."

    tool_call = msg.tool_calls[0]

    op_id = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")

    print("----- TOOL CALL -----")
    print(op_id)
    print(args)

    if op_id in {"getEmployeeShifts", "getScheduleShifts"}:
        if op_id == "getEmployeeShifts" and "employeeId" not in args:
            if explicit_employee_id is not None:
                args["employeeId"] = explicit_employee_id
            elif last_employee_id is not None:
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

    if op_id in {"createEmployee", "updateEmployee", "deleteEmployee"} and memory is not None:
        if hasattr(memory, "save_employee_directory"):
            memory.save_employee_directory(None)
        else:
            setattr(memory, "employee_directory", None)

    if op_id == "getEmployeeShifts":
        if memory is not None and args.get("employeeId") is not None:
            if hasattr(memory, "save_last_employee"):
                memory.save_last_employee(args["employeeId"])
            else:
                setattr(memory, "last_employee_id", args["employeeId"])
        employee_full_name = None
        target_employee_id = args.get("employeeId")
        if target_employee_id is not None and current_employee_id is not None and target_employee_id == current_employee_id:
            employee_full_name = "you"
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
