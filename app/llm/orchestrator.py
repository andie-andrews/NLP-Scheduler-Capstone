import json
import os
from datetime import datetime, timedelta
from openai import OpenAI

from .schemas import Intent
from .prompts import SYSTEM_PROMPT
from . import tools


# -------------------------------
# 🔑 OpenAI Client
# -------------------------------
def get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------
# 📅 Helpers
# -------------------------------
def normalize_schedule(data):
    if not data:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return data.get("data", [])

    return []


def find_matching_shifts(shifts, intent):
    if intent.date:
        return [s for s in shifts if intent.date in s.get("start", "")]
    return shifts


# -------------------------------
# Employee Resolution 
# -------------------------------
def resolve_employee(intent, role, token, session_employee_id, memory):
    """
    Determines which employee the request is targeting.
    """

    # No name → it's "me"
    if not intent.employee_name:
        return {"id": session_employee_id, "is_self": True}

    # Employees cannot query others
    if role == "Employee":
        return None

    employees = tools.get_employee_by_name(token, intent.employee_name)

    if not employees:
        return {"error": f"No employee found for {intent.employee_name}"}

    if len(employees) > 1:
        memory.save_intent(intent)
        memory.save_disambiguation("employee", employees)
        return {"disambiguation": employees}

    emp = employees[0]
    emp["is_self"] = emp["id"] == session_employee_id
    return emp


# -------------------------------
# Intent Parsing
# -------------------------------
def parse_intent(user_input: str, role: str):
    client = get_client()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    role=role,
                    schema=Intent.model_json_schema()
                ),
            },
            {"role": "user", "content": user_input},
        ],
        temperature=0,
    )

    content = response.choices[0].message.content
    return Intent(**json.loads(content))


# -------------------------------
# 🚀 MAIN ORCHESTRATOR
# -------------------------------
DEFAULT_SCHEDULE_ID = 12  # 🔥 TEMP for demo


def handle_request(user_input: str, role: str, token: str, memory, employee_id):

    # -------------------------------
    # MEMORY (follow-ups)
    # -------------------------------
    if memory.last_options:
        text = user_input.lower()

        index_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3
        }

        for key, idx in index_map.items():
            if key in text and len(memory.last_options) > idx:
                selected = memory.last_options[idx]
                intent = memory.last_intent

                if memory.last_entity_type == "employee":
                    tools.create_shift(
                        token,
                        DEFAULT_SCHEDULE_ID,
                        selected["id"],
                        intent.date,
                        intent.time,
                        intent.duration_hours,
                    )
                    memory.clear_disambiguation()
                    return f"Shift scheduled for {selected.get('firstName')}."

                if memory.last_entity_type == "shift":
                    if intent.action == "delete_shift":
                        tools.delete_shift(token, selected["id"])
                        memory.clear_disambiguation()
                        return "Shift deleted."

                memory.clear_disambiguation()

    # -------------------------------
    # 🧠 PARSE INTENT
    # -------------------------------
    intent = parse_intent(user_input, role)

    # -------------------------------
    # 👤 RESOLVE TARGET EMPLOYEE
    # -------------------------------
    target = resolve_employee(intent, role, token, employee_id, memory)

    if not target:
        return "You can only perform actions for yourself."

    if "error" in target:
        return target["error"]

    if "disambiguation" in target:
        return {
            "type": "disambiguation",
            "options": target["disambiguation"]
        }

    target_id = target["id"]
    is_self = target.get("is_self", False)
    name = "You" if is_self else target.get("firstName", "They")

    # -------------------------------
    # 📅 NEXT SHIFT
    # -------------------------------
    if intent.action == "get_my_next_shift":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, target_id, 0)
        )

        if not shifts:
            return f"{name} have no upcoming shifts."

        next_shift = sorted(shifts, key=lambda x: x.get("start", ""))[0]

        return f"{name} next shift is on {next_shift.get('start')} for {next_shift.get('durationHours')} hours."

    # -------------------------------
    # 📊 HOURS THIS WEEK
    # -------------------------------
    if intent.action == "get_my_hours_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, target_id, 0)
        )

        total = sum(s.get("durationHours", 0) for s in shifts)

        return f"{name} are scheduled for {total} hours this week."

    # -------------------------------
    #  DAYS WORKED
    # -------------------------------
    if intent.action == "get_my_days_worked_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, target_id, 0)
        )

        days = set(s.get("start", "")[:10] for s in shifts if s.get("start"))

        return f"{name} are working {len(days)} days this week."

    # -------------------------------
    # LIST SHIFTS WEEK
    # -------------------------------
    if intent.action == "list_my_shifts_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, target_id, 0)
        )

        return shifts if shifts else f"{name} have no shifts this week."

    # -------------------------------
    # LIST NEXT WEEK
    # -------------------------------
    if intent.action == "list_my_shifts_next_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, target_id, 1)
        )

        return shifts if shifts else f"{name} have no shifts next week."

    # -------------------------------
    # CREATE SHIFT
    # -------------------------------
    if intent.action == "create_shift":
        print("DEBUG: Creating shift with target:", target)
        tools.create_shift(
            token,
            DEFAULT_SCHEDULE_ID,
            target.get('id'),
            intent.date,
            intent.time,
            intent.duration_hours,
        )

        return f"Shift scheduled for Employee:{target.get('id')} - {target.get('fullName')} on schedule:{DEFAULT_SCHEDULE_ID}."

    # -------------------------------
    # ❌ DELETE SHIFT
    # -------------------------------
    if intent.action == "delete_shift":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, target_id, 0)
        )

        matches = find_matching_shifts(shifts, intent)

        if not matches:
            return "No matching shift found."

        if len(matches) > 1:
            memory.save_intent(intent)
            memory.save_disambiguation("shift", matches)

            return {"type": "disambiguation", "options": matches}

        tools.delete_shift(token, matches[0]["id"])
        return "Shift deleted."

    # -------------------------------
    # FALLBACK
    # -------------------------------
    if role in ["Supervisor", "Manager"]:
        return "Try: 'Schedule John Monday at 8am for 8 hours'"

    return "Sorry, I didn’t understand that."