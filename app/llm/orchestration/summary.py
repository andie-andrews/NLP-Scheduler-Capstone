def summarize_shifts(shifts, message: str):
    if not shifts:
        return {
            "summary": "No shifts found.",
            "totalHours": 0,
            "shifts": shifts
        }

    total_hours = sum(s.get("durationHours", 0) for s in shifts)
    msg = message.lower()

    if "how many hours" in msg or "total hours" in msg:
        return {
            "summary": f"Total scheduled hours: {total_hours}",
            "totalHours": total_hours,
            "shifts": shifts
        }

    if "next shift" in msg:
        next_shift = min(shifts, key=lambda x: x["start"])
        return {
            "summary": f"Next shift starts at {next_shift['start']}",
            "nextShift": next_shift,
            "shifts": shifts
        }

    return {
        "summary": f"Found {len(shifts)} shifts totaling {total_hours} hours.",
        "totalHours": total_hours,
        "shifts": shifts
    }
