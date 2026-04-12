from datetime import datetime

from app.llm.orchestration.parsers import extract_recurring_shift_dates, extract_time_range


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
