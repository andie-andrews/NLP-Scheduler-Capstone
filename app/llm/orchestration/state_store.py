PENDING_CREATE_SHIFT_KEY = "pending_create_shift"
PENDING_DELETE_SHIFT_KEY = "pending_delete_shift"
PENDING_SHOW_SHIFTS_KEY = "pending_show_shifts"
PENDING_UPDATE_SHIFT_KEY = "pending_update_shift"
PENDING_EMPLOYEE_DISAMBIGUATION_KEY = "pending_employee_disambiguation"
PENDING_SCHEDULE_MEMBER_CHANGE_KEY = "pending_schedule_member_change"
PENDING_CREATE_SCHEDULE_KEY = "pending_create_schedule"
PENDING_DELETE_SCHEDULE_KEY = "pending_delete_schedule"
PENDING_EMPLOYEE_OPERATION_KEY = "pending_employee_operation"


def _get_memory(session: dict):
    if session is None:
        return None
    return session.get("memory", session)


def _read_memory_value(memory, key: str):
    if memory is None:
        return None
    if isinstance(memory, dict):
        return memory.get(key)
    return getattr(memory, key, None)


def _write_memory_value(memory, key: str, value):
    if memory is None:
        return
    if isinstance(memory, dict):
        memory[key] = value
        return
    setattr(memory, key, value)


def _get_pending_state(session, key: str):
    return _read_memory_value(_get_memory(session), key)


def _set_pending_state(session, key: str, state):
    _write_memory_value(_get_memory(session), key, state)


def has_any_pending_state(session, keys: list[str]) -> bool:
    """Return True when any pending-state key is set in the current session memory."""
    return any(_get_pending_state(session, key) is not None for key in keys)


def get_pending_shift_state(session):
    return _get_pending_state(session, PENDING_CREATE_SHIFT_KEY)


def set_pending_shift_state(session, state):
    _set_pending_state(session, PENDING_CREATE_SHIFT_KEY, state)


def clear_pending_shift_state(session):
    set_pending_shift_state(session, None)


def get_pending_delete_shift_state(session):
    return _get_pending_state(session, PENDING_DELETE_SHIFT_KEY)


def set_pending_delete_shift_state(session, state):
    _set_pending_state(session, PENDING_DELETE_SHIFT_KEY, state)


def clear_pending_delete_shift_state(session):
    set_pending_delete_shift_state(session, None)


def get_pending_show_shifts_state(session):
    return _get_pending_state(session, PENDING_SHOW_SHIFTS_KEY)


def set_pending_show_shifts_state(session, state):
    _set_pending_state(session, PENDING_SHOW_SHIFTS_KEY, state)


def clear_pending_show_shifts_state(session):
    set_pending_show_shifts_state(session, None)


def get_pending_update_shift_state(session):
    return _get_pending_state(session, PENDING_UPDATE_SHIFT_KEY)


def set_pending_update_shift_state(session, state):
    _set_pending_state(session, PENDING_UPDATE_SHIFT_KEY, state)


def clear_pending_update_shift_state(session):
    set_pending_update_shift_state(session, None)


def get_pending_employee_disambiguation_state(session):
    return _get_pending_state(session, PENDING_EMPLOYEE_DISAMBIGUATION_KEY)


def set_pending_employee_disambiguation_state(session, state):
    _set_pending_state(session, PENDING_EMPLOYEE_DISAMBIGUATION_KEY, state)


def clear_pending_employee_disambiguation_state(session):
    set_pending_employee_disambiguation_state(session, None)


def get_pending_schedule_member_change_state(session):
    return _get_pending_state(session, PENDING_SCHEDULE_MEMBER_CHANGE_KEY)


def set_pending_schedule_member_change_state(session, state):
    _set_pending_state(session, PENDING_SCHEDULE_MEMBER_CHANGE_KEY, state)


def clear_pending_schedule_member_change_state(session):
    set_pending_schedule_member_change_state(session, None)


def get_pending_create_schedule_state(session):
    return _get_pending_state(session, PENDING_CREATE_SCHEDULE_KEY)


def set_pending_create_schedule_state(session, state):
    _set_pending_state(session, PENDING_CREATE_SCHEDULE_KEY, state)


def clear_pending_create_schedule_state(session):
    set_pending_create_schedule_state(session, None)


def get_pending_delete_schedule_state(session):
    return _get_pending_state(session, PENDING_DELETE_SCHEDULE_KEY)


def set_pending_delete_schedule_state(session, state):
    _set_pending_state(session, PENDING_DELETE_SCHEDULE_KEY, state)


def clear_pending_delete_schedule_state(session):
    set_pending_delete_schedule_state(session, None)


def get_pending_employee_operation_state(session):
    return _get_pending_state(session, PENDING_EMPLOYEE_OPERATION_KEY)


def set_pending_employee_operation_state(session, state):
    _set_pending_state(session, PENDING_EMPLOYEE_OPERATION_KEY, state)


def clear_pending_employee_operation_state(session):
    set_pending_employee_operation_state(session, None)
