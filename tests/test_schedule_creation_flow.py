from llm.orchestration.apps.scheduling.flows.pending_schedule_flow import handle_pending_schedule_flow


def test_pending_create_schedule_creates_group_and_clears_state():
    cleared = {"value": False}
    calls = []

    def clear_pending(_session):
        cleared["value"] = True

    def fake_call_api(_token, operation, args):
        calls.append((operation, args))
        return {"id": 42}

    result = handle_pending_schedule_flow(
        message="Create manager group Kitchen Leads",
        token="t",
        session={},
        pending_create_schedule={"intent": "create_schedule", "awaiting": "name"},
        pending_delete_schedule=None,
        operations={"createScheduleGroup": "create-schedule-op"},
        call_api=fake_call_api,
        clear_pending_create_schedule_state=clear_pending,
        clear_pending_delete_schedule_state=lambda *_: None,
        extract_schedule_name_or_id_from_message=lambda *_: None,
        extract_schedule_name_for_create=lambda *_: "Kitchen Leads",
        normalize_schedule_id_arg=lambda *_: None,
        lookup_schedule_name_by_id=lambda *_: None,
    )

    assert calls == [("create-schedule-op", {"name": "Kitchen Leads"})]
    assert cleared["value"] is True
    assert result == "Done — created schedule group Kitchen Leads (ID: 42)."


def test_pending_create_schedule_prompts_for_name_when_missing():
    result = handle_pending_schedule_flow(
        message="",
        token="t",
        session={},
        pending_create_schedule={"intent": "create_schedule", "awaiting": "name"},
        pending_delete_schedule=None,
        operations={"createScheduleGroup": "create-schedule-op"},
        call_api=lambda *_: (_ for _ in ()).throw(AssertionError("call_api should not be called")),
        clear_pending_create_schedule_state=lambda *_: None,
        clear_pending_delete_schedule_state=lambda *_: None,
        extract_schedule_name_or_id_from_message=lambda *_: None,
        extract_schedule_name_for_create=lambda *_: None,
        normalize_schedule_id_arg=lambda *_: None,
        lookup_schedule_name_by_id=lambda *_: None,
    )

    assert result == "What should I name the new schedule group?"
