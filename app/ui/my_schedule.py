import streamlit as st
from api_client import get_my_schedule
from collections import defaultdict
from datetime import datetime

def render():
    st.subheader("My Schedule")

    res = get_my_schedule()

    if res.status_code != 200:
        st.error("Failed to load schedule")
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

def get_schedules():
    return get("/api/schedules")

def get_schedule_employees(schedule_id):
    return get(f"/api/schedules/{schedule_id}/employees")

def get_schedule_shifts(schedule_id):
    return get(f"/api/schedules/{schedule_id}/shifts")

def create_shift(schedule_id, employee_id, start, duration):
    return post(
        f"/api/schedules/{schedule_id}/shifts",
        {
            "employeeId": employee_id,
            "start": start,
            "durationHours": duration
        }
    )