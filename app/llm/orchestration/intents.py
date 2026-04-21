import re

DEFAULT_CREATE_SHIFT_INTENT_KEYWORDS = [
    "create shift",
    "schedule a shift",
    "schedule shift",
    "assign shift",
]


def is_create_shift_intent(message: str, create_shift_operation: dict | None = None):
    text = (message or "").lower()
    openapi_keywords = (create_shift_operation or {}).get("intent_phrases") or []
    keywords = [k.strip().lower() for k in (openapi_keywords or DEFAULT_CREATE_SHIFT_INTENT_KEYWORDS) if k]

    def phrase_matches(phrase: str):
        words = [w for w in re.split(r"\W+", phrase.lower()) if w]
        return bool(words) and all(word in text for word in words)

    if any(phrase_matches(keyword) for keyword in keywords):
        return True

    looks_like_schedule_lookup = (
        bool(re.search(r"\b(what|show|view|see|list|which)\b", text))
        and "schedule" in text
    ) or bool(re.search(r"\b\w+['’]s schedule\b", text))
    if looks_like_schedule_lookup:
        return False

    weekday_terms = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "week",
        "today",
        "tomorrow",
        "tonight",
    ]
    has_weekday_context = any(term in text for term in weekday_terms)
    has_scheduling_action = any(action in text for action in ["schedule", "assign", "book"])
    if has_scheduling_action and has_weekday_context:
        has_shift_specific_context = (
            "shift" in text
            or "employee" in text
            or bool(re.search(r"\b(on|in|for)\s+.+\bschedule\b", text))
            or bool(re.search(r"\bschedule\s+(?!a\b|an\b|the\b)[a-z]+(?:\s+[a-z]+)?\b", text))
        )
        if has_shift_specific_context:
            return True

    return "shift" in text and any(action in text for action in ["schedule", "create", "assign"])


def is_delete_shift_intent(message: str):
    text = message.lower()
    has_delete_action = any(action in text for action in ["delete", "remove", "cancel"])
    return has_delete_action and "shift" in text


def is_update_shift_intent(message: str):
    text = message.lower()
    has_update_action = any(action in text for action in ["update", "edit", "change", "move", "reschedule", "reassign"])
    return has_update_action and "shift" in text


def _mentions_schedule_group(text: str) -> bool:
    return (
        "schedule group" in text
        or "schedule groups" in text
        or "manager group" in text
        or "manager groups" in text
    )


def is_create_schedule_intent(message: str):
    text = (message or "").lower()
    if not _mentions_schedule_group(text):
        return False
    if "shift" in text:
        return False
    return any(action in text for action in ["create", "new", "make"])


def is_add_schedule_member_intent(message: str):
    text = (message or "").lower()
    if not _mentions_schedule_group(text):
        return False
    add_words = any(word in text for word in ["add", "assign", "include", "put"])
    member_words = any(word in text for word in ["employee", "manager", "supervisor"])
    explicit_member_phrase = bool(re.search(r"\b(add|assign|include|put)\b.+\bto\b.+\bschedule group", text))
    return add_words and (explicit_member_phrase or member_words)


def is_remove_schedule_member_intent(message: str):
    text = (message or "").lower()
    if not _mentions_schedule_group(text):
        return False
    remove_words = any(word in text for word in ["remove", "unassign", "delete", "take off"])
    explicit_member_phrase = bool(re.search(r"\b(remove|unassign|delete|take off)\b.+\b(from|off)\b.+\bschedule group", text))
    member_words = any(word in text for word in ["employee", "staff member", "teammate"])
    return remove_words and (explicit_member_phrase or member_words)


def is_delete_schedule_intent(message: str):
    text = (message or "").lower()
    has_delete_action = any(action in text for action in ["delete", "remove", "cancel"])
    if not has_delete_action or not _mentions_schedule_group(text):
        return False
    if "shift" in text:
        return False
    return not is_remove_schedule_member_intent(message)


def is_get_manager_schedule_groups_intent(message: str):
    text = (message or "").lower()
    has_lookup = any(word in text for word in ["show", "list", "get", "view", "which", "what"])
    if not has_lookup:
        return False
    return (
        "manager groups" in text
        or "manager group" in text
        or "manageable schedule groups" in text
        or "groups i can manage" in text
    )


def is_create_employee_intent(message: str):
    text = (message or "").lower()
    if "employee" not in text:
        return False
    return any(action in text for action in ["create", "add", "new", "hire"])


def is_update_employee_intent(message: str):
    text = (message or "").lower()
    if "employee" not in text:
        return False
    return any(action in text for action in ["update", "edit", "change"])


def is_delete_employee_intent(message: str):
    text = (message or "").lower()
    if "employee" not in text:
        return False
    return any(action in text for action in ["delete", "remove", "terminate"])


def is_schedule_domain_message(message: str):
    text = (message or "").lower()
    if not text.strip():
        return False

    if any(
        intent_check(message)
        for intent_check in [
            is_create_shift_intent,
            is_delete_shift_intent,
            is_update_shift_intent,
            is_create_schedule_intent,
            is_add_schedule_member_intent,
            is_remove_schedule_member_intent,
            is_delete_schedule_intent,
            is_get_manager_schedule_groups_intent,
            is_create_employee_intent,
            is_update_employee_intent,
            is_delete_employee_intent,
        ]
    ):
        return True

    schedule_keywords = [
        "schedule",
        "shift",
        "shifts",
        "hours",
        "timesheet",
        "roster",
        "employee id",
        "manager",
        "supervisor",
        "staffing",
    ]
    return any(keyword in text for keyword in schedule_keywords)
