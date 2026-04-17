from app.llm.orchestration.intents import is_create_shift_intent


def test_is_create_shift_intent_with_schedule_as_verb_and_weekday_context():
    assert is_create_shift_intent("Schedule John Doe next week Monday-Friday") is True


def test_is_create_shift_intent_still_false_for_non_shift_schedule_context():
    assert is_create_shift_intent("Schedule a meeting tomorrow") is False


def test_is_create_shift_intent_false_for_schedule_noun_lookup():
    assert is_create_shift_intent("what is John Doe's schedule next week") is False


def test_is_create_shift_intent_with_relative_day_and_no_shift_word():
    assert is_create_shift_intent("Schedule Emma on Hostesses schedule tomorrow 4 PM to 10 PM") is True


def test_is_create_shift_intent_supports_common_temporal_misspellings():
    assert is_create_shift_intent("Schedule Emma on Hostesses schedule tomorow 4 PM to 10 PM next wek") is True
