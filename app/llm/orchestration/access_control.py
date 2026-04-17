import re

ACCESS_GUARD_MESSAGE = (
    "Sorry, I can't complete the task — you either do not have access "
    "or I am unable to determine your intent."
)


def is_supervisor(session: dict | None) -> bool:
    role = str((session or {}).get("role", "")).strip().lower()
    return role == "supervisor"


def _extract_referenced_employee_id(lowered_message: str) -> int | None:
    match = re.search(r"\b(?:employee|associate|worker)\s+(\d+)\b", lowered_message)
    if not match:
        return None
    return int(match.group(1))


def looks_like_other_employee_schedule_request(
    message: str, requester_employee_id: int | None = None
) -> bool:
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

    referenced_employee_id = _extract_referenced_employee_id(lowered)
    if referenced_employee_id is not None:
        if requester_employee_id is not None and referenced_employee_id == requester_employee_id:
            return False
        return True

    if re.search(r"\b(?:for|of)\s+[a-z]+(?:\s+[a-z]+)?\s+(?:schedule|shifts?)\b", lowered):
        return True

    return False
