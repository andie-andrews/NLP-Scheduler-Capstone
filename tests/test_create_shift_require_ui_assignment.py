import os

os.environ.setdefault("OPENAI_API_KEY", "dummy")

from llm import orchestrator


def test_create_shift_question_requires_ui_when_employee_has_no_schedule():
    state = {
        "intent": "create_shift",
        "employeeId": 101,
        "scheduleGroupId": None,
        "employee_schedule_options": [],
        "available_schedule_options": [{"id": 5, "name": "Kitchen"}],
    }

    question = orchestrator._build_create_shift_question(state)

    assert question == (
        "I can't create a shift yet because this employee is not on any schedule. "
        "Please add the employee to a schedule in the Manage Schedule Groups UI, then try again."
    )
