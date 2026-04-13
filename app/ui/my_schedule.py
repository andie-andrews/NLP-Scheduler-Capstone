from collections import defaultdict
from datetime import datetime, timedelta

import streamlit as st

from api_client import get_my_schedule
from ui.theme import render_page_header


def render():
    st.markdown(
        """
        <style>
            .st-key-my_schedule_scroll_body {
                flex: 1;
                min-height: 0;
                overflow-y: auto;
                overflow-x: hidden;
                padding-right: 0.35rem;
                padding-bottom: 0.5rem;
            }

            .st-key-my_schedule_scroll_body::-webkit-scrollbar {
                width: 10px;
            }

            .st-key-my_schedule_scroll_body::-webkit-scrollbar-thumb {
                background: rgba(120, 120, 120, 0.45);
                border-radius: 999px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_page_header("My Schedule", "View your weekly shifts with clear day-by-day summaries.")

    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0

    employee_id = st.session_state["employee_id"]

    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    if nav_col1.button("◀ Previous", use_container_width=True):
        st.session_state["week_offset"] -= 1
    if nav_col3.button("Next ▶", use_container_width=True):
        st.session_state["week_offset"] += 1

    today = datetime.today()
    base_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    start_of_week = base_week + timedelta(weeks=st.session_state["week_offset"])
    end_of_week = start_of_week + timedelta(days=6)

    nav_col2.markdown(
        f"<div class='metric-tile' style='text-align:center;font-weight:600;'>Week of {start_of_week.strftime('%b %d, %Y')}</div>",
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
        st.info("No shifts this week.")
        return

    days = defaultdict(list)
    total_hours = 0

    for shift in shifts:
        dt = datetime.fromisoformat(shift["start"])
        day = dt.strftime("%A (%Y-%m-%d)")
        days[day].append(shift)
        total_hours += int(shift.get("durationHours", 0))

    c1, c2 = st.columns(2)
    c1.metric("Total shifts", len(shifts))
    c2.metric("Total hours", total_hours)

    with st.container(key="my_schedule_scroll_body"):
        for day, items in sorted(days.items()):
            st.markdown(f"<div class='section-card'><b>{day}</b></div>", unsafe_allow_html=True)
            for s in items:
                start = datetime.fromisoformat(s["start"])
                end = start + timedelta(hours=s["durationHours"])
                schedule_name = s.get("scheduleName")
                schedule_suffix = f" · **{schedule_name}**" if schedule_name else ""
                st.markdown(
                    f"- **{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}** ({s['durationHours']} hrs){schedule_suffix}"
                )
