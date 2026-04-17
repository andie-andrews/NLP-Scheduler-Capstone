from app.llm.orchestration.access_control import (
    is_supervisor,
    looks_like_other_employee_schedule_request,
)


def test_is_supervisor_true_when_role_is_supervisor_case_insensitive():
    assert is_supervisor({"role": "Supervisor"}) is True


def test_is_supervisor_false_for_employee_role():
    assert is_supervisor({"role": "employee"}) is False


def test_other_employee_possessive_schedule_request_is_detected():
    assert looks_like_other_employee_schedule_request("Show me Jane's schedule this week") is True


def test_self_schedule_request_is_not_detected_as_other_employee():
    assert looks_like_other_employee_schedule_request("Show me my schedule this week") is False


def test_temporal_phrase_next_weeks_schedule_is_not_detected_as_other_employee():
    assert looks_like_other_employee_schedule_request("Show next week's schedule") is False


def test_employee_id_reference_is_detected_as_other_employee_request():
    assert looks_like_other_employee_schedule_request("Get shifts for employee 105") is True
