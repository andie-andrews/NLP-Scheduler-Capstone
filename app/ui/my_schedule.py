import streamlit as st
from api_client import get_my_schedule
from collections import defaultdict
from datetime import datetime, timedelta

def render():
    st.subheader("My Schedule")
     # 🔥 INIT STATE
    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0
    employee_id = st.session_state["employee_id"]

     # 🔹 WEEK NAV
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

    if nav_col1.button("◀"):
        st.session_state["week_offset"] -= 1

    if nav_col3.button("▶"):
        st.session_state["week_offset"] += 1

    today = datetime.today()
    base_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    start_of_week = base_week + timedelta(weeks=st.session_state["week_offset"])
    days = [start_of_week + timedelta(days=i) for i in range(7)]

    nav_col2.markdown(
        f"<div style='text-align:center;font-size:20px;font-weight:600;'>Week of {start_of_week.strftime('%b %d, %Y')}</div>",
        unsafe_allow_html=True
    )

    res = get_my_schedule(employee_id,
                          params={"weekStart": start_of_week.isoformat()})

    if res.status_code != 200:
        st.error(f"Failed to load schedule {employee_id} - {res.text}")
        return

    shifts = res.json()

    if not shifts:
        st.info("No shifts this week")
        return

    # group by day
    days = defaultdict(list)

    for shift in shifts:
        dt = datetime.fromisoformat(shift["start"])
        day = dt.strftime("%A (%Y-%m-%d)")
        days[day].append(shift)

    # render
    for day, items in days.items():
        st.markdown(f"### {day}")

        for s in items:
            start = datetime.fromisoformat(s["start"])
            st.write(f"{start.strftime('%I:%M %p')} - {s['durationHours']} hrs")

