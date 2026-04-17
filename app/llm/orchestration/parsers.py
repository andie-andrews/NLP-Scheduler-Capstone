import re
from datetime import datetime, timedelta


TEMPORAL_MISSPELLINGS = {
    "wek": "week",
    "weks": "weeks",
    "tomorow": "tomorrow",
    "tommorow": "tomorrow",
    "tmrw": "tomorrow",
}


def normalize_temporal_text(message: str):
    text = (message or "").lower()
    for misspelling, correction in TEMPORAL_MISSPELLINGS.items():
        text = re.sub(rf"\b{re.escape(misspelling)}\b", correction, text)
    return text


def find_name_in_message(message: str, employees: list):
    message_lower = normalize_temporal_text(message)
    employee_records = employees
    if isinstance(employee_records, dict):
        for key in ("items", "employees", "results", "data", "value", "content"):
            candidate = employee_records.get(key)
            if isinstance(candidate, list):
                employee_records = candidate
                break
        else:
            employee_records = []
    if not isinstance(employee_records, list):
        return None

    # Pass 1: prefer explicit full-name matches anywhere in the utterance.
    for emp in employee_records:
        if not isinstance(emp, dict):
            continue
        full_name = f"{emp.get('firstName') or ''} {emp.get('lastName') or ''}".strip().lower()
        if full_name and full_name in message_lower:
            return full_name

    # Pass 2: fallback to first-name matches only when no full name matched.
    for emp in employee_records:
        if not isinstance(emp, dict):
            continue
        first_name = (emp.get("firstName") or "").strip().lower()
        if first_name and first_name in message_lower:
            return first_name

    return None


def extract_duration_hours(message: str):
    match = re.search(r"(\d+)\s*(hour|hours|hr|hrs)\b", normalize_temporal_text(message))
    if not match:
        return None
    return int(match.group(1))


def extract_time_of_day(message: str):
    text = normalize_temporal_text(message)
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
    text = normalize_temporal_text(message)
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
    text = normalize_temporal_text(message)
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
    weekday_aliases = {
        "monday": ["monday", "mon"],
        "tuesday": ["tuesday", "tue", "tues"],
        "wednesday": ["wednesday", "wed"],
        "thursday": ["thursday", "thu", "thur", "thurs"],
        "friday": ["friday", "fri"],
        "saturday": ["saturday", "sat"],
        "sunday": ["sunday", "sun"],
    }

    alias_to_weekday = {
        alias: canonical
        for canonical, aliases in weekday_aliases.items()
        for alias in aliases
    }

    def list_from_weekday_expression(expression: str):
        values = []
        for alias, canonical_name in alias_to_weekday.items():
            if re.search(rf"\b{alias}\b", expression):
                values.append(weekdays[canonical_name])
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

    weekday_pattern = r"(?:monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)"
    range_match = re.search(
        rf"\b({weekday_pattern})\b\s*"
        r"(?:-|–|through|thru|to)\s*"
        rf"\b({weekday_pattern})\b",
        normalized,
    )
    if range_match:
        start_day = weekdays[alias_to_weekday[range_match.group(1)]]
        end_day = weekdays[alias_to_weekday[range_match.group(2)]]
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
        dates = [target_week_start + timedelta(days=(weekday + 1) % 7) for weekday in span]
        if "next week" not in normalized and "this week" not in normalized:
            if dates and dates[-1] < now.date():
                dates = [date + timedelta(days=7) for date in dates]
        return dates

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


def _extract_relative_date(text: str, now: datetime):
    normalized = normalize_temporal_text(text)
    if "tomorrow" in normalized:
        return now + timedelta(days=1)
    if "today" in normalized or "tonight" in normalized:
        return now
    return None


def extract_weekday_datetime(message: str, now: datetime | None = None):
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    text = normalize_temporal_text(message)
    target_day = None
    for name, idx in weekdays.items():
        if name in text:
            target_day = idx
            break

    now = now or datetime.now()
    relative_date = _extract_relative_date(text, now)
    if relative_date is not None:
        parsed_time = extract_time_of_day(text)
        if not parsed_time:
            print("[create_shift][datetime] Relative date found but no explicit time in message.")
            return None
        hour, minute = parsed_time
        start = relative_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return start.isoformat()

    if target_day is None:
        print("[create_shift][datetime] No weekday found in message.")
        return None

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
    text = normalize_temporal_text(message)
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
    # Preserve raw schedule identifiers and only normalize case. Applying temporal
    # typo normalization here can rewrite legitimate entity names (e.g. "Wek").
    normalized_message = (message or "").lower()
    patterns = [
        r"(?:to|on|in)\s+([a-zA-Z0-9 _'’-]+?)['’]s\s+schedule\b",
        r"(?:from)\s+([a-zA-Z0-9 _'’-]+?)['’]s\s+schedule\b",
        r"^([a-zA-Z0-9 _'’-]+?)['’]s\s+schedule\b",
        r"(?:on|in|from)\s+([a-zA-Z0-9 _'’-]+?)\s+schedule\b",
        r"schedule\s+(?:for|on|in|from)\s+([a-zA-Z0-9 _'’-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized_message)
        if match:
            schedule_name = match.group(1).strip(" .,!?:;\"'")
            schedule_name = re.sub(r"^(the|a|an)\s+", "", schedule_name, flags=re.IGNORECASE)
            return schedule_name.strip()
    return None


def extract_weekday_date(message: str, now: datetime | None = None):
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    text = normalize_temporal_text(message)
    target_day = None
    for name, idx in weekdays.items():
        if name in text:
            target_day = idx
            break

    now = now or datetime.now()
    relative_date = _extract_relative_date(text, now)
    if target_day is None:
        return relative_date.date() if relative_date is not None else None

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
