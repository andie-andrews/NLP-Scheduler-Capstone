from app.llm.orchestration.intents import (
    is_create_schedule_intent,
    is_get_manager_schedule_groups_intent,
    is_schedule_domain_message,
    is_update_shift_intent,
)


def test_is_create_schedule_intent_false_when_message_is_about_shift_creation():
    message = "Create a shift for Kai Grill on Tuesday from 9:00 AM to 5:00 PM on the Kitchen schedule."
    assert is_create_schedule_intent(message) is False


def test_is_create_schedule_intent_true_for_actual_schedule_creation():
    assert is_create_schedule_intent("Create schedule group Kitchen") is True


def test_is_create_schedule_intent_false_without_explicit_schedule_group_phrase():
    assert is_create_schedule_intent("Create a new Kitchen schedule") is False


def test_is_schedule_domain_message_true_for_shift_question():
    assert is_schedule_domain_message("How many hours am I working next week?") is True


def test_is_schedule_domain_message_false_for_general_chat():
    assert is_schedule_domain_message("Tell me a joke about coffee.") is False


def test_is_update_shift_intent_true_for_reassign_shift_message():
    assert is_update_shift_intent("reassign shift on monday for john to jane") is True


def test_is_get_manager_schedule_groups_intent_true_for_manager_group_lookup():
    assert is_get_manager_schedule_groups_intent("Show me my manager groups") is True


def test_is_create_schedule_intent_true_for_manager_group_creation_phrase():
    assert is_create_schedule_intent("Create manager group Kitchen Leads") is True
