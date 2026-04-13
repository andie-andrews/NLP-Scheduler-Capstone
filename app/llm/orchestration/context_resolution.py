import re


def is_self_referential_employee_query(message: str):
    text = (message or "").lower()
    if not re.search(r"\b(my|me|i)\b", text):
        return False
    return bool(re.search(r"\b(week|month|shift|schedule|hours?)\b", text))


def is_follow_up_employee_query(message: str):
    text = (message or "").lower()
    has_subject = bool(re.search(r"\b(week|month|shift|schedule|hours?)\b", text))
    has_follow_up_phrase = bool(re.search(r"\b(next|this|what about|how many|scheduled|schedule)\b", text))
    return has_subject and has_follow_up_phrase
