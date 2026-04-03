import streamlit as st
from api_client import (
    get_schedules,
    get_schedule_employees,
    get_schedule_shifts,
    create_shift,
    create_schedule,
    update_schedule,
    delete_schedule
)
from datetime import datetime, timedelta
from collections import defaultdict


def render():

    # 🔥 HEADER (CLEAN + ICONS)
    header_col1, header_col2 = st.columns([6, 2])

    with header_col1:
        st.markdown("## Manage Schedules")

    with header_col2:
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            if st.button("➕", help="Create Schedule", use_container_width=True):
                st.session_state["show_create_schedule"] = True

        with btn_col2:
            if st.button("✎", help="Edit Schedule", use_container_width=True):
                st.session_state["show_edit_schedule"] = True

        with btn_col3:
            if st.button("🗑️", help="Delete Schedule", use_container_width=True):
                st.session_state["show_delete_schedule"] = True

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # 🔹 Load schedules
    res = get_schedules()
    if res.status_code != 200:
        st.error("Failed to load schedules")
        return

    schedules = res.json()

    if not schedules:
        st.info("No schedules available")
        return

    schedule_map = {s["name"]: s["id"] for s in schedules}

    # 🔹 Select schedule
    selected_name = st.selectbox("Select Schedule", list(schedule_map.keys()))
    schedule_id = schedule_map[selected_name]

    # 🔥 WEEK STATE
    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0

    # 🔹 NAVIGATION (CENTERED)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

    with nav_col1:
        if st.button("◀", use_container_width=True):
            st.session_state["week_offset"] -= 1

    with nav_col3:
        if st.button("▶", use_container_width=True):
            st.session_state["week_offset"] += 1

    today = datetime.today()
    base_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    start_of_week = base_week + timedelta(weeks=st.session_state["week_offset"])
    days = [start_of_week + timedelta(days=i) for i in range(7)]

    with nav_col2:
        st.markdown(
            f"""
            <div style="text-align:center;">
                <div style="font-size:14px;color:#aaa;">Schedule</div>
                <div style="font-size:22px;font-weight:600;">
                    Week of {start_of_week.strftime('%b %d, %Y')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 🔹 Load employees
    emp_res = get_schedule_employees(schedule_id)
    employees = emp_res.json() if emp_res.status_code == 200 else []

    # 🔹 Load shifts
    shift_res = get_schedule_shifts(
        schedule_id,
        params={"weekStart": start_of_week.isoformat()}
    )
    shifts = shift_res.json() if shift_res.status_code == 200 else []

    # 🔹 Group shifts
    shift_lookup = defaultdict(list)
    for s in shifts:
        date_key = s["start"][:10]
        shift_lookup[(s["employeeId"], date_key)].append(s)

    # 🔹 Totals
    day_totals = defaultdict(int)

    # 🔹 HEADER ROW
    header = st.columns(8)
    header[0].markdown("**Employee**")

    for i, day in enumerate(days):
        header[i + 1].markdown(
            f"""
            <div style="text-align:center;">
                <div style="font-size:13px;color:#aaa;">
                    {day.strftime('%a')}
                </div>
                <div style="font-weight:600;">
                    {day.strftime('%m/%d')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border:0.5px solid #333;'>", unsafe_allow_html=True)

    # 🔹 ROWS
    for emp in employees:
        full_name = f"{emp['firstName']} {emp['lastName']}"

        employee_total = 0
        for day in days:
            key = (emp["id"], day.strftime("%Y-%m-%d"))
            if key in shift_lookup:
                for shift in shift_lookup[key]:
                    employee_total += shift["durationHours"]
                    day_totals[day.strftime("%Y-%m-%d")] += shift["durationHours"]

        row = st.columns(8)

        # 🔥 INLINE TOTAL
        row[0].markdown(f"**{full_name} ({employee_total}h)**")

        for i, day in enumerate(days):
            day_str = day.strftime("%Y-%m-%d")
            key = (emp["id"], day_str)

            with row[i + 1]:

                if key in shift_lookup:
                    for shift in shift_lookup[key]:
                        start_dt = datetime.fromisoformat(shift["start"])
                        end_dt = start_dt + timedelta(hours=shift["durationHours"])

                        st.markdown(
                            f"""
                            <div style="
                                background: linear-gradient(135deg, #2c2f36, #3a3f47);
                                padding:8px;
                                margin:6px 0;
                                border-radius:8px;
                                font-size:12px;
                                border:1px solid #444;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                            ">
                                <div style="font-weight:600;">
                                    {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}
                                </div>
                                <div style="color:#bbb;">
                                    {shift['durationHours']}h
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

                if st.button("＋", key=f"add_{emp['id']}_{day_str}", use_container_width=True):
                    create_shift(
                        schedule_id,
                        emp["id"],
                        day.replace(hour=8, minute=0).isoformat(),
                        8
                    )
                    st.rerun()

        st.markdown("<hr style='border:0.5px solid #222;'>", unsafe_allow_html=True)

    # 🔹 FOOTER TOTALS
    footer = st.columns(8)

    footer[0].markdown(
        "<div style='color:#aaa;'>Totals</div>",
        unsafe_allow_html=True
    )

    for i, day in enumerate(days):
        total = day_totals[day.strftime("%Y-%m-%d")]

        footer[i + 1].markdown(
            f"""
            <div style="text-align:center;font-weight:600;">
                {total}h
            </div>
            """,
            unsafe_allow_html=True
        )

    # 🔹 CREATE SCHEDULE
    if st.session_state.get("show_create_schedule"):
        with st.form("create_schedule"):
            st.subheader("Create Schedule")
            name = st.text_input("Schedule Name")

            if st.form_submit_button("Create"):
                res = create_schedule(name)
                if res.status_code == 200:
                    st.success("Created")
                    st.session_state["show_create_schedule"] = False
                    st.rerun()

    # 🔹 EDIT SCHEDULE
    if st.session_state.get("show_edit_schedule"):
        with st.form("edit_schedule"):
            st.subheader("Edit Schedule")
            new_name = st.text_input("Name", value=selected_name)

            if st.form_submit_button("Save"):
                res = update_schedule(schedule_id, new_name)
                if res.status_code == 200:
                    st.success("Updated")
                    st.session_state["show_edit_schedule"] = False
                    st.rerun()

    # 🔹 DELETE SCHEDULE
    if st.session_state.get("show_delete_schedule"):
        st.warning(f"Delete '{selected_name}'?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Confirm Delete"):
                res = delete_schedule(schedule_id)
                if res.status_code == 200:
                    st.success("Deleted")
                    st.session_state["show_delete_schedule"] = False
                    st.rerun()

        with col2:
            if st.button("Cancel"):
                st.session_state["show_delete_schedule"] = False