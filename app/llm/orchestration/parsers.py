import re
from datetime import datetime, timedelta


def find_name_in_message(message: str, employees: list):
    message_lower = message.lower()

    for emp in employees:
        full_name = f"{emp['firstName']} {emp['lastName']}".lower()
        first_name = emp['firstName'].lower()

        if full_name in message_lower:
            return full_name

        if first_name in message_lower:
            return first_name

    return None


def extract_duration_hours(message: str):
    match = re.search(r"(\d+)\s*(hour|hours|hr|hrs)\b", message.lower())
    if not match:
        return None
    return int(match.group(1))


def extract_time_of_day(message: str):
    text = (message or "").lower()
    time_match = re.search(r"(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text)
    if not time_match:
        return None

    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    meridian = (time_match.group(3) or "").lower()

    if meridian == "pm" and hour != 12:
        hour += 12
    if meridian == "am" and hour == 12:
        hour = 0

    if hour > 23 or minute > 59:
        return None

    return hour, minute


def extract_weekday_datetime(message: str):
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    text = message.lower()
    target_day = None
    for name, idx in weekdays.items():
        if name in text:
            target_day = idx
            break

    if target_day is None:
        print("[create_shift][datetime] No weekday found in message.")
        return None

    now = datetime.now()

    if re.search(r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text):
        delta = (target_day - now.weekday()) % 7
        if delta == 0:
            delta = 7
        delta += 7
    elif re.search(r"\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text):
        delta = target_day - now.weekday()
    else:
        delta = (target_day - now.weekday()) % 7

    target_date = now + timedelta(days=delta)

    parsed_time = extract_time_of_day(text)
    if not parsed_time:
        print("[create_shift][datetime] Weekday found but no explicit time in message.")
        return None
    hour, minute = parsed_time

    start = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    print(
        "[create_shift][datetime] Parsed start:",
        {
            "message": message,
            "target_day": target_day,
            "delta_days": delta,
            "hour": hour,
            "minute": minute,
            "iso_start": start.isoformat(),
        },
    )
    return start.isoformat()


def week_range_from_date(target: datetime):
    days_since_sunday = (target.weekday() + 1) % 7
    start = (target - timedelta(days=days_since_sunday)).date()
    end = start + timedelta(days=6)
    return start, end


def extract_week_range_from_message(message: str, now: datetime | None = None):
    text = (message or "").lower()
    now = now or datetime.now()

    if "this week" in text:
        start, end = week_range_from_date(now)
        return {"startDate": start.isoformat(), "endDate": end.isoformat()}

    if "next week" in text:
        start, end = week_range_from_date(now + timedelta(days=7))
        return {"startDate": start.isoformat(), "endDate": end.isoformat()}

    if "this month" in text:
        month_start = now.replace(day=1).date()
        if now.month == 12:
            next_month_start = now.replace(year=now.year + 1, month=1, day=1).date()
        else:
            next_month_start = now.replace(month=now.month + 1, day=1).date()
        month_end = next_month_start - timedelta(days=1)
        return {"startDate": month_start.isoformat(), "endDate": month_end.isoformat()}

    return None


def extract_schedule_name(message: str):
    patterns = [
        r"(?:on|in)\s+([a-zA-Z0-9 _'’-]+?)\s+schedule",
        r"schedule\s+(?:for|on|in)?\s*([a-zA-Z0-9 _'’-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return match.group(1).strip(" .,!?:;\"'")
    return None


def extract_weekday_date(message: str):
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    text = message.lower()
    target_day = None
    for name, idx in weekdays.items():
        if name in text:
            target_day = idx
            break

    if target_day is None:
        return None

    now = datetime.now()
    if re.search(r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text):
        delta = (target_day - now.weekday()) % 7
        if delta == 0:
            delta = 7
        delta += 7
    elif re.search(r"\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text):
        delta = target_day - now.weekday()
    else:
        delta = (target_day - now.weekday()) % 7

    return (now + timedelta(days=delta)).date()


def format_shift_option_line(index: int, shift: dict):
    start = datetime.fromisoformat(shift["start"])
    return f"{index}. {start.strftime('%I:%M %p')} for {shift.get('durationHours', 0)} hours"


def get_week_start():
    today = datetime.today()
    days_since_sunday = (today.weekday() + 1) % 7
    start = today - timedelta(days=days_since_sunday)
    return start.strftime("%m/%d/%Y")
