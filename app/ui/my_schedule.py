from collections import defaultdict
from datetime import datetime, timedelta

import streamlit as st

from api_client import get_my_schedule
from ui.styles import render_page_header


def render():
    render_page_header("My Schedule", "Review your weekly shifts and total scheduled hours.")

    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0

    employee_id = st.session_state["employee_id"]

    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

    if nav_col1.button("◀", use_container_width=True):
        st.session_state["week_offset"] -= 1

    if nav_col3.button("▶", use_container_width=True):
        st.session_state["week_offset"] += 1

    today = datetime.today()
    base_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    start_of_week = base_week + timedelta(weeks=st.session_state["week_offset"])
    end_of_week = start_of_week + timedelta(days=6)

    nav_col2.markdown(
        f"<div style='text-align:center;font-size:20px;font-weight:600;'>Week of {start_of_week.strftime('%b %d, %Y')}</div>",
        unsafe_allow_html=True,
    )

    res = get_my_schedule(
        employee_id,
        params={
            "startDate": start_of_week.date().isoformat(),
            "endDate": end_of_week.date().isoformat(),
        },
    )

    if res.status_code != 200:
        st.error(f"Failed to load schedule {employee_id} - {res.text}")
        return

    shifts = res.json()

    if not shifts:
        st.info("No shifts this week")
        return

    shifts_by_day = defaultdict(list)
    total_hours = 0

    for shift in shifts:
        dt = datetime.fromisoformat(shift["start"])
        day_key = dt.date().isoformat()
        shifts_by_day[day_key].append(shift)
        total_hours += shift.get("durationHours", 0)

    col1, col2 = st.columns(2)
    col1.metric("Total Hours", total_hours)
    col2.metric("Total Shifts", len(shifts))

    st.markdown("### Daily Breakdown")

    ordered_days = [start_of_week + timedelta(days=i) for i in range(7)]
    for day in ordered_days:
        day_key = day.date().isoformat()
        items = shifts_by_day.get(day_key, [])

        st.markdown(
            f"<div class='app-card'><strong>{day.strftime('%A, %b %d')}</strong></div>",
            unsafe_allow_html=True,
        )

        if not items:
            st.caption("No shifts")
            continue

        for shift in sorted(items, key=lambda i: i["start"]):
            start = datetime.fromisoformat(shift["start"])
            end = start + timedelta(hours=shift["durationHours"])
            st.markdown(
                f"<span class='app-pill'>{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}</span>"
                f"<span class='app-pill'>{shift['durationHours']} hrs</span>",
                unsafe_allow_html=True,
            )
