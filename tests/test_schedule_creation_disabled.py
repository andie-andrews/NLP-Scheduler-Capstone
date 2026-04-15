from app.llm.orchestration.flows.pending_schedule_flow import handle_pending_schedule_flow


def test_pending_create_schedule_redirects_to_ui_and_clears_state():
    cleared = {"value": False}

    def clear_pending(_session):
        cleared["value"] = True

    result = handle_pending_schedule_flow(
        message="Kitchen",
        token="t",
        session={},
        pending_create_schedule={"intent": "create_schedule", "awaiting": "name"},
        pending_delete_schedule=None,
        operations={"createSchedule": "create-schedule-op"},
        call_api=lambda *_: (_ for _ in ()).throw(AssertionError("call_api should not be called")),
        clear_pending_create_schedule_state=clear_pending,
        clear_pending_delete_schedule_state=lambda *_: None,
        extract_schedule_name_or_id_from_message=lambda *_: None,
        normalize_schedule_id_arg=lambda *_: None,
        lookup_schedule_name_by_id=lambda *_: None,
    )

    assert cleared["value"] is True
    assert result == "Schedule creation is only available in the Manage Schedules UI."
