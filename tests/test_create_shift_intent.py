from app.llm.orchestration.intents import is_create_shift_intent


def test_is_create_shift_intent_with_schedule_as_verb_and_weekday_context():
    assert is_create_shift_intent("Schedule John Doe next week Monday-Friday") is True


def test_is_create_shift_intent_still_false_for_non_shift_schedule_context():
    assert is_create_shift_intent("Schedule a meeting tomorrow") is False


def test_is_create_shift_intent_false_for_schedule_noun_lookup():
    assert is_create_shift_intent("what is John Doe's schedule next week") is False
