from app.llm.orchestration.parsers import extract_schedule_name


def test_extract_schedule_name_strips_leading_article():
    message = "Create a shift for Kai Grill on Tuesday from 9:00 AM to 5:00 PM on the Kitchen schedule."
    assert extract_schedule_name(message) == "kitchen"


def test_extract_schedule_name_without_article():
    message = "Create shift for Kai on Kitchen schedule"
    assert extract_schedule_name(message) == "kitchen"


def test_extract_schedule_name_does_not_apply_temporal_typo_normalization():
    message = "Show schedule for Wek"
    assert extract_schedule_name(message) == "wek"
