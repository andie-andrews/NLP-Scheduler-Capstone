from app.llm.orchestration.intents import is_create_schedule_intent


def test_is_create_schedule_intent_false_when_message_is_about_shift_creation():
    message = "Create a shift for Kai Grill on Tuesday from 9:00 AM to 5:00 PM on the Kitchen schedule."
    assert is_create_schedule_intent(message) is False


def test_is_create_schedule_intent_true_for_actual_schedule_creation():
    assert is_create_schedule_intent("Create a new Kitchen schedule") is True
