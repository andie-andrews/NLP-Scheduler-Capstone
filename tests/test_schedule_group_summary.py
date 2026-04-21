from llm.orchestration.summary import summarize_manager_schedule_groups, summarize_schedule_groups


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


def test_summarize_manager_schedule_groups_with_multiple_results():
    result = summarize_manager_schedule_groups(
        [
            {"id": 4, "name": "Bartenders"},
            {"id": 2, "name": "Hostesses"},
            {"id": 3, "name": "Kitchen"},
        ]
    )

    assert result["summary"] == "You manage 3 schedule groups: Bartenders, Hostesses, and Kitchen."
    assert len(result["groups"]) == 3
