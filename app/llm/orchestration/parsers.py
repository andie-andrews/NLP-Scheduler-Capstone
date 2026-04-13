import re
from datetime import datetime, timedelta


def find_name_in_message(message: str, employees: list):
    message_lower = (message or "").lower()

    # Pass 1: prefer explicit full-name matches anywhere in the utterance.
    for emp in employees:
        full_name = f"{emp['firstName']} {emp['lastName']}".strip().lower()
        if full_name and full_name in message_lower:
            return full_name

    # Pass 2: fallback to first-name matches only when no full name matched.
    for emp in employees:
        first_name = (emp.get("firstName") or "").strip().lower()
        if first_name and first_name in message_lower:
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


def extract_time_range(message: str):
    text = (message or "").lower()
    match = re.search(
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:-|to)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
        text,
    )
    if not match:
        return None

    def to_24_hour(raw_hour: str, raw_minute: str | None, meridian: str | None):
        hour = int(raw_hour)
        minute = int(raw_minute or 0)
        marker = (meridian or "").lower()
        if marker == "pm" and hour != 12:
            hour += 12
        if marker == "am" and hour == 12:
            hour = 0
        if marker not in {"am", "pm"} and hour == 24:
            hour = 0
        if hour > 23 or minute > 59:
            return None
        return hour, minute

    start_meridian = match.group(3)
    end_meridian = match.group(6)
    if not start_meridian and end_meridian:
        start_meridian = end_meridian

    start = to_24_hour(match.group(1), match.group(2), start_meridian)
    end = to_24_hour(match.group(4), match.group(5), end_meridian)
    if not start or not end:
        return None

    start_minutes = start[0] * 60 + start[1]
    end_minutes = end[0] * 60 + end[1]
    if end_minutes <= start_minutes:
        end_minutes += 24 * 60

    duration_minutes = end_minutes - start_minutes
    if duration_minutes % 60 != 0:
        return None

    return {"startHour": start[0], "startMinute": start[1], "durationHours": duration_minutes // 60}


def extract_recurring_shift_dates(message: str, now: datetime | None = None):
    text = (message or "").lower()
    now = now or datetime.now()
    normalized = re.sub(r"\s+", " ", text)

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    def list_from_weekday_expression(expression: str):
        values = []
        for day_name, day_index in weekdays.items():
            if re.search(rf"\b{day_name}\b", expression):
                values.append(day_index)
        return sorted(set(values))

    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
    }

    range_match = re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b\s*"
        r"(?:-|–|through|thru|to)\s*"
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        normalized,
    )
    if range_match and ("next week" in normalized or "this week" in normalized):
        start_day = weekdays[range_match.group(1)]
        end_day = weekdays[range_match.group(2)]
        span = []
        day = start_day
        while True:
            span.append(day)
            if day == end_day:
                break
            day = (day + 1) % 7

        days_since_sunday = (now.weekday() + 1) % 7
        start_of_this_week = (now - timedelta(days=days_since_sunday)).date()
        week_offset = 7 if "next week" in normalized else 0
        target_week_start = start_of_this_week + timedelta(days=week_offset)
        return [target_week_start + timedelta(days=(weekday + 1) % 7) for weekday in span]

    every_match = re.search(
        r"\bevery\s+(.+?)\s+for\s+(?:the\s+)?next\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+weeks?\b",
        normalized,
    )
    if every_match:
        days = list_from_weekday_expression(every_match.group(1))
        raw_weeks = every_match.group(2)
        weeks = int(raw_weeks) if raw_weeks.isdigit() else number_words.get(raw_weeks, 0)
        if not days or weeks <= 0:
            return None
        dates = []
        window_end = now.date() + timedelta(days=weeks * 7)
        current = now.date()
        while current < window_end:
            if current.weekday() in days:
                dates.append(current)
            current += timedelta(days=1)
        return dates

    return None


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
        r"(?:to|on|in)\s+([a-zA-Z0-9 _'’-]+?)['’]s\s+schedule\b",
        r"(?:from)\s+([a-zA-Z0-9 _'’-]+?)['’]s\s+schedule\b",
        r"^([a-zA-Z0-9 _'’-]+?)['’]s\s+schedule\b",
        r"(?:on|in|from)\s+([a-zA-Z0-9 _'’-]+?)\s+schedule\b",
        r"schedule\s+(?:for|on|in|from)\s+([a-zA-Z0-9 _'’-]+)",
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
    schedule_name = shift.get("scheduleName")
    schedule_phrase = f" ({schedule_name})" if schedule_name else ""
    return f"{index}. {start.strftime('%I:%M %p')} for {shift.get('durationHours', 0)} hours{schedule_phrase}"


def get_week_start():
    today = datetime.today()
    days_since_sunday = (today.weekday() + 1) % 7
    start = today - timedelta(days=days_since_sunday)
    return start.strftime("%m/%d/%Y")
