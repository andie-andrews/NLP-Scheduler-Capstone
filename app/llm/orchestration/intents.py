import re

DEFAULT_CREATE_SHIFT_INTENT_KEYWORDS = [
    "create shift",
    "schedule a shift",
    "schedule shift",
    "assign shift",
]


def is_create_shift_intent(message: str, create_shift_operation: dict | None = None):
    text = message.lower()
    openapi_keywords = (create_shift_operation or {}).get("intent_phrases") or []
    keywords = [k.strip().lower() for k in (openapi_keywords or DEFAULT_CREATE_SHIFT_INTENT_KEYWORDS) if k]

    def phrase_matches(phrase: str):
        words = [w for w in re.split(r"\W+", phrase.lower()) if w]
        return bool(words) and all(word in text for word in words)

    if any(phrase_matches(keyword) for keyword in keywords):
        return True

    return "shift" in text and any(action in text for action in ["schedule", "create", "assign"])


def is_delete_shift_intent(message: str):
    text = message.lower()
    has_delete_action = any(action in text for action in ["delete", "remove", "cancel"])
    return has_delete_action and "shift" in text


def is_update_shift_intent(message: str):
    text = message.lower()
    has_update_action = any(action in text for action in ["update", "edit", "change", "move", "reschedule"])
    return has_update_action and "shift" in text


def is_create_schedule_intent(message: str):
    text = (message or "").lower()
    if "schedule" not in text:
        return False
    if any(member_word in text for member_word in ["employee", "manager", "supervisor"]):
        return False
    return any(action in text for action in ["create", "new", "make"])


def is_add_schedule_member_intent(message: str):
    text = (message or "").lower()
    member_words = any(word in text for word in ["employee", "manager", "supervisor"])
    add_words = any(word in text for word in ["add", "assign", "include", "put"])
    return "schedule" in text and member_words and add_words


def is_remove_schedule_member_intent(message: str):
    text = (message or "").lower()
    member_words = any(word in text for word in ["employee", "manager", "supervisor"])
    remove_words = any(word in text for word in ["remove", "unassign", "delete", "take off"])
    return "schedule" in text and member_words and remove_words
