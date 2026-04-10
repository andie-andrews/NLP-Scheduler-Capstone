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
