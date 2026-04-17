import re

ACCESS_GUARD_MESSAGE = (
    "Sorry, I can't complete the task — you either do not have access "
    "or I am unable to determine your intent."
)


def is_supervisor(session: dict | None) -> bool:
    role = str((session or {}).get("role", "")).strip().lower()
    return role == "supervisor"


def looks_like_other_employee_schedule_request(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False

    lowered = text.lower()
    if not re.search(r"\b(schedule|shifts?)\b", lowered):
        return False

    if re.search(r"\b(my|mine|i am|i'm)\b", lowered):
        return False

    possessive_match = re.search(r"\b([a-z]+(?:\s+[a-z]+)?)['’]s\s+(?:schedule|shifts?)\b", lowered)
    if possessive_match:
        owner_token = possessive_match.group(1).strip()
        temporal_tokens = {"next", "this", "last", "week", "month", "today", "tomorrow", "yesterday"}
        owner_words = set(owner_token.split())
        if owner_words.isdisjoint(temporal_tokens):
            return True

    if re.search(r"\b(?:employee|associate|worker)\s+\d+\b", lowered):
        return True

    if re.search(r"\b(?:for|of)\s+[a-z]+(?:\s+[a-z]+)?\s+(?:schedule|shifts?)\b", lowered):
        return True

    return False
