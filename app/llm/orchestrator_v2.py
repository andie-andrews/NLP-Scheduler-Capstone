import json
import re
from datetime import datetime, timedelta
from openai import OpenAI

from llm.openapi_loader import load_openapi_spec
from llm.openapi_parser import parse_operations
from llm.openapi_client import call_api
from .prompts_v2 import SYSTEM_PROMPT, CALCULATION_RULES

client = OpenAI()

spec = load_openapi_spec()
OPERATIONS = parse_operations(spec)

DEFAULT_CREATE_SHIFT_INTENT_KEYWORDS = [
    "create shift",
    "schedule",
    "assign shift",
]


# -------------------------------
# 🔥 Employee Resolver
# -------------------------------
def resolve_employee_id(token, name):
    search_op = OPERATIONS.get("searchEmployees")

    if not search_op:
        return None

    results = call_api(token, search_op, {"query": name})

    if not results:
        return {"type": "not_found", "name": name}

    if len(results) == 1:
        return {"type": "resolved", "employeeId": results[0]["id"]}

    options = [
        f"{r['firstName']} {r['lastName']} (ID: {r['id']})"
        for r in results
    ]

    return {
        "type": "disambiguation",
        "options": options,
        "raw": results
    }


def resolve_schedule_id(token, name):
    schedule_op = OPERATIONS.get("getSchedules")

    if not schedule_op:
        return None

    schedules = call_api(token, schedule_op, {})
    if not schedules:
        return {"type": "not_found", "name": name}

    target = (name or "").strip().lower()
    if not target:
        return {"type": "not_found", "name": name}

    exact = [s for s in schedules if (s.get("name") or "").strip().lower() == target]
    if len(exact) == 1:
        return {"type": "resolved", "scheduleId": exact[0]["id"], "name": exact[0].get("name")}

    partial = [s for s in schedules if target in (s.get("name") or "").strip().lower()]
    if len(partial) == 1:
        return {"type": "resolved", "scheduleId": partial[0]["id"], "name": partial[0].get("name")}

    matches = exact or partial
    if matches:
        return {
            "type": "disambiguation",
            "options": [f"{s.get('name')} (ID: {s.get('id')})" for s in matches],
            "raw": matches
        }

    return {"type": "not_found", "name": name}


# -------------------------------
# 🔍 Find name in message
# -------------------------------
def find_name_in_message(message: str, employees: list):
    message_lower = message.lower()

    for emp in employees:
        full_name = f"{emp['firstName']} {emp['lastName']}".lower()
        first_name = emp['firstName'].lower()

        if full_name in message_lower:
            return full_name

        if first_name in message_lower:
            return first_name

    return None


def is_create_shift_intent(message: str):
    text = message.lower()
    create_shift_operation = OPERATIONS.get("createShift", {})
    openapi_keywords = create_shift_operation.get("intent_phrases") or []
    keywords = openapi_keywords or DEFAULT_CREATE_SHIFT_INTENT_KEYWORDS
    return any(keyword.lower() in text for keyword in keywords)


def extract_duration_hours(message: str):
    match = re.search(r"(\d+)\s*(hour|hours|hr|hrs)\b", message.lower())
    if not match:
        return None
    return int(match.group(1))


def extract_weekday_datetime(message: str):
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    text = message.lower()
    target_day = None
    for name, idx in weekdays.items():
        if name in text:
            target_day = idx
            break

    if target_day is None:
        return None

    now = datetime.now()
    delta = (target_day - now.weekday()) % 7
    if delta == 0:
        delta = 7
    start = (now + timedelta(days=delta)).replace(hour=9, minute=0, second=0, microsecond=0)
    return start.isoformat()


def extract_schedule_name(message: str):
    patterns = [
        r"(?:on|in)\s+([a-zA-Z0-9 _-]+?)\s+schedule",
        r"schedule\s+([a-zA-Z0-9 _-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return match.group(1).strip()
    return None


def _get_pending_shift_state(session):
    memory = session.get("memory")
    if memory is None:
        return None
    return getattr(memory, "pending_create_shift", None)


def _set_pending_shift_state(session, state):
    memory = session.get("memory")
    if memory is None:
        return
    setattr(memory, "pending_create_shift", state)


def _clear_pending_shift_state(session):
    _set_pending_shift_state(session, None)


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


def _attempt_fill_shift_state_from_message(message, token, state):
    employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""})
    name = find_name_in_message(message, employees) if employees else None
    if name and not state.get("employeeId"):
        resolution = resolve_employee_id(token, name)
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

    schedule_name = extract_schedule_name(message)
    if schedule_name and not state.get("scheduleId"):
        schedule_resolution = resolve_schedule_id(token, schedule_name)
        if schedule_resolution and schedule_resolution.get("type") == "resolved":
            state["scheduleId"] = schedule_resolution["scheduleId"]
        elif schedule_resolution and schedule_resolution.get("type") == "disambiguation":
            state["schedule_options"] = schedule_resolution["raw"]
            state["awaiting"] = "schedule_disambiguation"
            return {
                "type": "disambiguation",
                "entity": "schedule",
                "options": schedule_resolution["options"],
            }

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


# -------------------------------
# 🔧 Tool Builder
# -------------------------------
def build_tools():
    tools = []

    for op_id, op in OPERATIONS.items():

        properties = {}
        required = []

        for param in op.get("parameters", []):
            name = param["name"]
            properties[name] = {
                "type": param.get("schema", {}).get("type", "string"),
                "description": param.get("description", "")
            }

            if param.get("required"):
                required.append(name)

        if op.get("requestBody"):
            content = op["requestBody"]["content"]["application/json"]["schema"]

            for prop, details in content.get("properties", {}).items():
                properties[prop] = {
                    "type": details.get("type", "string")
                }

            required += content.get("required", [])

        tools.append({
            "type": "function",
            "function": {
                "name": op_id,
                "description": op["summary"] or op_id,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        })

    return tools


# -------------------------------
# 🧠 Prompt Builder
# -------------------------------
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

weekStart:
- If not provided, default to the current week

DO NOT return text if a function can be called.
ONLY return tool calls.
"""

    return SYSTEM_PROMPT + "\n\n" + context + "\n\n" + tool_rules + "\n\n" + CALCULATION_RULES


# -------------------------------
# 🔢 Shift Summary Logic
# -------------------------------
def summarize_shifts(shifts, message: str):
    if not shifts:
        return {
            "summary": "No shifts found.",
            "totalHours": 0,
            "shifts": shifts
        }

    total_hours = sum(s.get("durationHours", 0) for s in shifts)
    msg = message.lower()

    if "how many hours" in msg or "total hours" in msg:
        return {
            "summary": f"Total scheduled hours: {total_hours}",
            "totalHours": total_hours,
            "shifts": shifts
        }

    if "next shift" in msg:
        next_shift = min(shifts, key=lambda x: x["start"])
        return {
            "summary": f"Next shift starts at {next_shift['start']}",
            "nextShift": next_shift,
            "shifts": shifts
        }

    return {
        "summary": f"Found {len(shifts)} shifts totaling {total_hours} hours.",
        "totalHours": total_hours,
        "shifts": shifts
    }


# -------------------------------
# 📅 Week helper
# -------------------------------
def get_week_start():
    today = datetime.today()
    start = today - timedelta(days=today.weekday())
    return start.strftime("%m/%d/%Y")


# -------------------------------
# 🚀 Orchestrator
# -------------------------------
def run_orchestrator(message: str, token: str, session: dict):

    print("----- USER MESSAGE -----")
    print(message)

    pending_shift = _get_pending_shift_state(session)
    if pending_shift and pending_shift.get("awaiting"):
        resolved = _resolve_disambiguation_reply(message, pending_shift)
        if resolved is None:
            pass
        elif resolved is False:
            options = pending_shift.get("employee_options") if pending_shift.get("awaiting") == "employee_disambiguation" else pending_shift.get("schedule_options")
            if not options:
                return "Please choose one of the listed options by number."
            lines = [f"{idx + 1}. {item.get('firstName', item.get('name', ''))} {item.get('lastName', '')}".strip() for idx, item in enumerate(options)]
            return "Please choose one option by number:\n" + "\n".join(lines)

    if pending_shift or is_create_shift_intent(message):
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
        _set_pending_shift_state(session, state)

        disambiguation = _attempt_fill_shift_state_from_message(message, token, state)
        if disambiguation:
            options = disambiguation["options"]
            option_lines = [f"{idx + 1}. {value}" for idx, value in enumerate(options)]
            entity = disambiguation["entity"]
            return f"I found multiple {entity}s. Please choose one:\n" + "\n".join(option_lines)

        question = _build_create_shift_question(state)
        if question:
            return question

        args = {
            "scheduleId": state["scheduleId"],
            "employeeId": state["employeeId"],
            "start": state["start"],
            "durationHours": state["durationHours"],
        }
        result = call_api(token, OPERATIONS["createShift"], args)
        _clear_pending_shift_state(session)
        return {
            "summary": "Shift created successfully.",
            "data": result
        }

    # 🔍 Get employees for matching
    employees = call_api(token, OPERATIONS["searchEmployees"], {"query": ""})

    name = find_name_in_message(message, employees)

    if name:
        resolution = resolve_employee_id(token, name)

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

    tools = build_tools()

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

    # 🔧 Ensure required defaults
    if op_id == "getEmployeeShifts":
        if "weekStart" not in args:
            args["weekStart"] = get_week_start()

    result = call_api(token, OPERATIONS[op_id], args)

    print("----- API RESULT -----")
    print(result)

    # 🔥 SMART POST PROCESSING
    if op_id == "getEmployeeShifts":
        summary_data = summarize_shifts(result, message)

        # Optional: natural language response
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
