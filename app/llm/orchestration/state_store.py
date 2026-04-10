PENDING_CREATE_SHIFT_KEY = "pending_create_shift"
PENDING_DELETE_SHIFT_KEY = "pending_delete_shift"
PENDING_SHOW_SHIFTS_KEY = "pending_show_shifts"


def _get_memory(session: dict):
    return session.get("memory") if session else None


def get_pending_shift_state(session):
    memory = _get_memory(session)
    if memory is None:
        return None
    return getattr(memory, PENDING_CREATE_SHIFT_KEY, None)


def set_pending_shift_state(session, state):
    memory = _get_memory(session)
    if memory is None:
        return
    setattr(memory, PENDING_CREATE_SHIFT_KEY, state)


def clear_pending_shift_state(session):
    set_pending_shift_state(session, None)


def get_pending_delete_shift_state(session):
    memory = _get_memory(session)
    if memory is None:
        return None
    return getattr(memory, PENDING_DELETE_SHIFT_KEY, None)


def set_pending_delete_shift_state(session, state):
    memory = _get_memory(session)
    if memory is None:
        return
    setattr(memory, PENDING_DELETE_SHIFT_KEY, state)


def clear_pending_delete_shift_state(session):
    set_pending_delete_shift_state(session, None)


def get_pending_show_shifts_state(session):
    memory = _get_memory(session)
    if memory is None:
        return None
    return getattr(memory, PENDING_SHOW_SHIFTS_KEY, None)


def set_pending_show_shifts_state(session, state):
    memory = _get_memory(session)
    if memory is None:
        return
    setattr(memory, PENDING_SHOW_SHIFTS_KEY, state)


def clear_pending_show_shifts_state(session):
    set_pending_show_shifts_state(session, None)
