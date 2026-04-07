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
# 🧠 Intent Parsing
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
DEFAULT_SCHEDULE_ID = 1  # 🔥 TEMP for demo

def handle_request(user_input: str, role: str, token: str, memory, employee_id):

    # -------------------------------
    # 🔁 MEMORY (follow-ups)
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
    # 🔒 ROLE GUARDRAILS
    # -------------------------------
    if role == "Employee" and intent.employee_name:
        return "You can only perform actions for yourself."

    # -------------------------------
    # 📅 NEXT SHIFT
    # -------------------------------
    if intent.action == "get_my_next_shift":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, employee_id, 0)
        )

        if not shifts:
            return "You have no upcoming shifts."

        next_shift = sorted(shifts, key=lambda x: x.get("start", ""))[0]

        return f"Your next shift is on {next_shift.get('start')} for {next_shift.get('durationHours')} hours."

    # -------------------------------
    # 📊 HOURS THIS WEEK
    # -------------------------------
    if intent.action == "get_my_hours_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, employee_id, 0)
        )

        total = sum(s.get("durationHours", 0) for s in shifts)
        return f"You are scheduled for {total} hours this week."

    # -------------------------------
    # 📆 DAYS WORKED
    # -------------------------------
    if intent.action == "get_my_days_worked_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, employee_id, 0)
        )

        days = set(s.get("start", "")[:10] for s in shifts if s.get("start"))
        return f"You are working {len(days)} days this week."

    # -------------------------------
    # 📋 LIST SHIFTS WEEK
    # -------------------------------
    if intent.action == "list_my_shifts_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, employee_id, 0)
        )

        return shifts if shifts else "You have no shifts this week."

    # -------------------------------
    # 📋 LIST NEXT WEEK
    # -------------------------------
    if intent.action == "list_my_shifts_next_week":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, employee_id, 1)
        )

        return shifts if shifts else "You have no shifts next week."

    # -------------------------------
    # ➕ CREATE SHIFT
    # -------------------------------
    if intent.action == "create_shift":
        employees = tools.get_employee_by_name(intent.employee_name)

        if not employees:
            return f"No employee found for {intent.employee_name}."

        if len(employees) > 1:
            memory.save_intent(intent)
            memory.save_disambiguation("employee", employees)

            return {
                "type": "disambiguation",
                "options": employees
            }

        emp = employees[0]

        tools.create_shift(
            token,
            DEFAULT_SCHEDULE_ID,
            emp["id"],
            intent.date,
            intent.time,
            intent.duration_hours,
        )

        return f"Shift scheduled for {emp.get('firstName')}."

    # -------------------------------
    # ❌ DELETE SHIFT
    # -------------------------------
    if intent.action == "delete_shift":
        shifts = normalize_schedule(
            tools.get_employee_shifts(token, employee_id, 0)
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
    # ❓ FALLBACK
    # -------------------------------
    if role in ["Supervisor", "Manager"]:
        return "Try: 'Schedule John Monday at 8am for 8 hours'"

    return "Sorry, I didn’t understand that."