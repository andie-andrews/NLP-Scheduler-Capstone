import streamlit as st
from api_client import get_my_schedule
from collections import defaultdict
from datetime import datetime, timedelta

def render():
    st.subheader("My Schedule")
    st.caption("Review your weekly shifts and total hours at a glance.")
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
    end_of_week = start_of_week + timedelta(days=6)
    days = [start_of_week + timedelta(days=i) for i in range(7)]

    nav_col2.markdown(
        f"<div style='text-align:center;font-size:20px;font-weight:600;'>Week of {start_of_week.strftime('%b %d, %Y')}</div>",
        unsafe_allow_html=True
    )

    res = get_my_schedule(employee_id,
                          params={
                              "startDate": start_of_week.date().isoformat(),
                              "endDate": end_of_week.date().isoformat(),
                          })

    if res.status_code != 200:
        st.error(f"Failed to load schedule {employee_id} - {res.text}")
        return

    shifts = res.json()

    if not shifts:
        st.info("No shifts this week")
        return

    total_hours = sum(shift.get("durationHours", 0) for shift in shifts)
    top_cols = st.columns(2)
    top_cols[0].metric("Shifts This Week", len(shifts))
    top_cols[1].metric("Total Hours", total_hours)

    # group by day
    days = defaultdict(list)

    for shift in shifts:
        dt = datetime.fromisoformat(shift["start"])
        day = dt.strftime("%A (%Y-%m-%d)")
        days[day].append(shift)

    # render
    for day, items in days.items():
        day_total = sum(shift.get("durationHours", 0) for shift in items)
        with st.expander(f"{day} • {day_total} hrs", expanded=True):
            for s in sorted(items, key=lambda shift: shift["start"]):
                start = datetime.fromisoformat(s["start"])
                end = start + timedelta(hours=s["durationHours"])
                st.markdown(
                    f"- **{start.strftime('%I:%M %p')} – {end.strftime('%I:%M %p')}** ({s['durationHours']} hrs)"
                )
