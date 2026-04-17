from datetime import datetime

from app.llm.orchestration.parsers import (
    extract_recurring_shift_dates,
    extract_time_range,
    extract_weekday_date,
    extract_weekday_datetime,
)


def test_extract_time_range_with_meridian():
    parsed = extract_time_range("Monday-Friday 9am-5pm")
    assert parsed == {"startHour": 9, "startMinute": 0, "durationHours": 8}


def test_extract_recurring_shift_dates_next_week_weekday_span():
    now = datetime(2026, 4, 12, 12, 0, 0)
    dates = extract_recurring_shift_dates("Schedule Jane next week Monday-Friday 9am-5pm", now=now)
    assert [d.isoformat() for d in dates] == [
        "2026-04-20",
        "2026-04-21",
        "2026-04-22",
        "2026-04-23",
        "2026-04-24",
    ]


def test_extract_recurring_shift_dates_every_two_days_for_weeks():
    now = datetime(2026, 4, 12, 12, 0, 0)
    dates = extract_recurring_shift_dates("Every Tuesday and Wednesday for the next six weeks", now=now)
    assert len(dates) == 12
    assert dates[0].isoformat() == "2026-04-14"
    assert dates[-1].isoformat() == "2026-05-20"


def test_extract_recurring_shift_dates_weekday_span_when_next_week_comes_last():
    now = datetime(2026, 4, 12, 12, 0, 0)
    dates = extract_recurring_shift_dates("Create shifts for John Doe Monday-Friday next week", now=now)
    assert [d.isoformat() for d in dates] == [
        "2026-04-20",
        "2026-04-21",
        "2026-04-22",
        "2026-04-23",
        "2026-04-24",
    ]


def test_extract_recurring_shift_dates_weekday_span_with_through_keyword():
    now = datetime(2026, 4, 12, 12, 0, 0)
    dates = extract_recurring_shift_dates("Create shifts Monday through Friday for John Doe next week", now=now)
    assert [d.isoformat() for d in dates] == [
        "2026-04-20",
        "2026-04-21",
        "2026-04-22",
        "2026-04-23",
        "2026-04-24",
    ]


def test_extract_recurring_shift_dates_weekday_span_without_week_qualifier():
    now = datetime(2026, 4, 14, 12, 0, 0)
    dates = extract_recurring_shift_dates("Create shifts for Lori Monday-Friday", now=now)
    assert [d.isoformat() for d in dates] == [
        "2026-04-13",
        "2026-04-14",
        "2026-04-15",
        "2026-04-16",
        "2026-04-17",
    ]


def test_extract_recurring_shift_dates_weekday_span_supports_abbreviations():
    now = datetime(2026, 4, 14, 12, 0, 0)
    dates = extract_recurring_shift_dates("Create shifts for Lori Mon-Fri", now=now)
    assert [d.isoformat() for d in dates] == [
        "2026-04-13",
        "2026-04-14",
        "2026-04-15",
        "2026-04-16",
        "2026-04-17",
    ]


def test_extract_weekday_date_supports_tomorrow():
    now = datetime(2026, 4, 15, 12, 0, 0)
    parsed = extract_weekday_date("tomorrow", now=now)
    assert parsed.isoformat() == "2026-04-16"


def test_extract_weekday_datetime_supports_tomorrow_with_time():
    now = datetime(2026, 4, 15, 12, 0, 0)
    parsed = extract_weekday_datetime("tomorrow 4pm", now=now)
    assert parsed == "2026-04-16T16:00:00"


def test_extract_weekday_datetime_supports_common_tomorrow_misspelling():
    now = datetime(2026, 4, 15, 12, 0, 0)
    parsed = extract_weekday_datetime("tomorow 4pm", now=now)
    assert parsed == "2026-04-16T16:00:00"


def test_extract_recurring_shift_dates_supports_common_week_misspelling():
    now = datetime(2026, 4, 12, 12, 0, 0)
    dates = extract_recurring_shift_dates("Schedule Jane next wek Monday-Friday 9am-5pm", now=now)
    assert [d.isoformat() for d in dates] == [
        "2026-04-20",
        "2026-04-21",
        "2026-04-22",
        "2026-04-23",
        "2026-04-24",
    ]
