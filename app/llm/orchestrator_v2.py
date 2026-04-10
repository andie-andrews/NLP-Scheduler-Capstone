import json
from datetime import datetime, timedelta
from openai import OpenAI

from llm.openapi_loader import load_openapi_spec
from llm.openapi_parser import parse_operations
from llm.openapi_client import call_api
from .prompts_v2 import SYSTEM_PROMPT, CALCULATION_RULES

client = OpenAI()

spec = load_openapi_spec()
OPERATIONS = parse_operations(spec)


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