from llm.orchestration.summary import summarize_schedule_groups


def test_summarize_schedule_groups_with_single_group_and_name():
    result = summarize_schedule_groups(
        [{"id": 2, "name": "Hostesses"}],
        employee_full_name="Emma Stone",
    )

    assert result["summary"] == "Emma Stone is in Hostesses."
    assert result["groups"] == [{"id": 2, "name": "Hostesses"}]


def test_summarize_schedule_groups_with_no_results():
    result = summarize_schedule_groups([], employee_full_name="Emma Stone")

    assert result["summary"] == "No schedule groups found for Emma Stone."
    assert result["groups"] == []
