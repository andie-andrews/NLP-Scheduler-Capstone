from datetime import datetime
import re


def _format_shift_datetime(iso_start: str):
    dt = datetime.fromisoformat(iso_start)
    return dt.strftime("%A, %b %d, %Y at %I:%M %p")


def _is_hours_question(msg: str):
    return "how many hours" in msg or "total hours" in msg or "hours" in msg


def _is_next_shift_question(msg: str):
    scheduled_next_patterns = [
        r"\bwhen\s+am\s+i\s+scheduled\s+next\b",
        r"\bwhen\s+is\s+.+?\s+scheduled\s+next\b",
        r"\bwhen\s+is\s+.+?'s\s+scheduled\s+next\b",
    ]

    return (
        "next shift" in msg
        or "next schedule" in msg
        or "when is my next schedule" in msg
        or any(re.search(pattern, msg) for pattern in scheduled_next_patterns)
    )


def summarize_shifts(shifts, message: str):
    if not shifts:
        return {
            "summary": "No shifts found.",
            "totalHours": 0,
            "shifts": shifts
        }

    total_hours = sum(s.get("durationHours", 0) for s in shifts)
    msg = message.lower()

    if _is_hours_question(msg) and "next week" in msg:
        return {
            "summary": f"You are scheduled for {total_hours} hours, would you like to see your shifts?",
            "totalHours": total_hours,
            "promptToShowShifts": True,
            "shifts": shifts,
        }

    if _is_hours_question(msg):
        return {
            "summary": f"Total scheduled hours: {total_hours}",
            "totalHours": total_hours,
            "shifts": shifts
        }

    if _is_next_shift_question(msg):
        now = datetime.now()
        upcoming = [s for s in shifts if datetime.fromisoformat(s["start"]) >= now]
        next_shift = min(upcoming or shifts, key=lambda x: x["start"])
        friendly_start = _format_shift_datetime(next_shift["start"])
        return {
            "summary": (
                f"Your next shift is on {friendly_start} for {next_shift.get('durationHours', 0)} hours. "
                "Would you like to see your shifts?"
            ),
            "totalHours": total_hours,
            "promptToShowShifts": True,
            "nextShift": next_shift,
            "shifts": shifts
        }

    return {
        "summary": f"Found {len(shifts)} shifts totaling {total_hours} hours.",
        "totalHours": total_hours,
        "shifts": shifts
    }
