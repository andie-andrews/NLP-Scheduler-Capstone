import streamlit as st
from api_client import (
    get_schedules,
    get_schedule_employees,
    get_schedule_shifts,
    create_shift,
    update_shift,
    delete_shift,
    create_schedule,
    update_schedule,
    delete_schedule,
    get_all_employees,
    add_employee_to_schedule,
    remove_employee_from_schedule
)
from datetime import datetime, timedelta
from collections import defaultdict


def render():

    # 🔥 INIT STATE
    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0
    if "pending_cell_shift" not in st.session_state:
        st.session_state["pending_cell_shift"] = None
    if "editing_shift" not in st.session_state:
        st.session_state["editing_shift"] = None
    if "deleting_shift" not in st.session_state:
        st.session_state["deleting_shift"] = None
    if "remove_schedule_employee" not in st.session_state:
        st.session_state["remove_schedule_employee"] = None

    # 🔥 HEADER
    header_col1, header_col2 = st.columns([6, 2])

    with header_col1:
        st.markdown("## Manage Schedules")

    with header_col2:
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        if btn_col1.button("➕", use_container_width=True):
            st.session_state["show_create_schedule"] = True

        if btn_col2.button("✎", use_container_width=True):
            st.session_state["show_edit_schedule"] = True

        if btn_col3.button("🗑️", use_container_width=True):
            st.session_state["show_delete_schedule"] = True

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # 🔹 LOAD SCHEDULES
    res = get_schedules()
    if res.status_code != 200:
        st.error("Failed to load schedules")
        return

    schedules = res.json()
    if not schedules:
        st.info("No schedules available")
        return

    schedule_map = {s["name"]: s["id"] for s in schedules}

    selected_name = st.selectbox("Select Schedule", list(schedule_map.keys()))
    schedule_id = schedule_map[selected_name]

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

    # 🔹 LOAD EMPLOYEES
    emp_res = get_schedule_employees(schedule_id)
    employees = emp_res.json() if emp_res.status_code == 200 else []

    # 🔥 LOAD ALL EMPLOYEES
    all_emp_res = get_all_employees()
    all_employees = all_emp_res.json() if all_emp_res.status_code == 200 else []

    # 🔥 ZERO STATE
    if not employees:
        st.info("No employees assigned to this schedule.")

        zero_key = f"zero_add_{schedule_id}_{len(employees)}"

        selected = st.selectbox(
            "Add employee",
            options=[None] + [e["id"] for e in all_employees],
            format_func=lambda x: "➕ Select employee..." if x is None else
            next(f"{e['firstName']} {e['lastName']}" for e in all_employees if e["id"] == x),
            key=zero_key
        )

        if selected:
            add_employee_to_schedule(schedule_id, selected)
            st.rerun()

        return

    # 🔹 LOAD SHIFTS
    shift_res = get_schedule_shifts(
        schedule_id,
        params={"weekStart": start_of_week.isoformat()}
    )
    shifts = shift_res.json() if shift_res.status_code == 200 else []

    shift_lookup = defaultdict(list)

    for s in shifts:
        date_key = s["start"][:10]
        shift_lookup[(s["employeeId"], date_key)].append(s)

    day_totals = defaultdict(int)

    # 🔹 HEADER
    header = st.columns(8)
    header[0].markdown("**Employee**")

    for i, day in enumerate(days):
        header[i + 1].markdown(
            f"<div style='text-align:center'>{day.strftime('%a %m/%d')}</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

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

        row = st.columns(9)

        row[0].markdown(f"**{full_name} ({employee_total}h)**")

        if row[1].button("❌", key=f"remove_{emp['id']}"):
            st.session_state["remove_schedule_employee"] = {
                "schedule_id": schedule_id,
                "employee_id": emp["id"],
                "employee_name": full_name
            }

        for i, day in enumerate(days):
            day_str = day.strftime("%Y-%m-%d")
            key = (emp["id"], day_str)

            with row[i + 2]:
                cell_id = f"{emp['id']}_{day_str}"

                with st.popover("Cell options", use_container_width=True):
                    st.caption(f"{full_name} • {day.strftime('%a %m/%d')}")

                    if st.button("Add shift", key=f"cell_add_shift_{cell_id}", use_container_width=True):
                        st.session_state["pending_cell_shift"] = {
                            "schedule_id": schedule_id,
                            "employee_id": emp["id"],
                            "employee_name": full_name,
                            "day_str": day_str
                        }
                        st.rerun()

                if key in shift_lookup:
                    for shift in shift_lookup[key]:
                        start_dt = datetime.fromisoformat(shift["start"])
                        end_dt = start_dt + timedelta(hours=shift["durationHours"])
                        shift_id = shift["id"]
                        shift_label = (
                            f"{start_dt.strftime('%I:%M %p')} - "
                            f"{end_dt.strftime('%I:%M %p')} ({shift['durationHours']}h)"
                        )

                        with st.popover(shift_label, use_container_width=True):
                            st.caption(f"{full_name} • {day.strftime('%a %m/%d')}")

                            if st.button("Edit shift", key=f"edit_shift_{shift_id}", use_container_width=True):
                                st.session_state["editing_shift"] = {
                                    "id": shift_id,
                                    "employee_name": full_name,
                                    "start": shift["start"],
                                    "durationHours": shift["durationHours"]
                                }
                                st.rerun()

                            if st.button("Delete shift", key=f"delete_shift_{shift_id}", use_container_width=True):
                                st.session_state["deleting_shift"] = {
                                    "id": shift_id,
                                    "employee_name": full_name,
                                    "start": shift["start"],
                                    "durationHours": shift["durationHours"]
                                }
                                st.rerun()

    # 🔹 FOOTER
    st.markdown("---")
    footer = st.columns(8)

    footer[0].markdown("Totals")

    for i, day in enumerate(days):
        total = day_totals[day.strftime("%Y-%m-%d")]
        footer[i + 1].markdown(f"**{total}h**")

    # 🔥 GHOST ROW
    assigned_ids = {emp["id"] for emp in employees}
    available = [e for e in all_employees if e["id"] not in assigned_ids]

    if available:

        ghost_key = f"ghost_add_{schedule_id}_{len(employees)}"

        ghost_row = st.columns(9)

        selected = ghost_row[0].selectbox(
            "",
            options=[None] + [e["id"] for e in available],
            format_func=lambda x: "➕ Add employee..." if x is None else
            next(f"{e['firstName']} {e['lastName']}" for e in available if e["id"] == x),
            key=ghost_key
        )

        if selected:
            add_employee_to_schedule(schedule_id, selected)
            selected = None
            st.rerun()

    # 🔥 MODALS (unchanged)

    if st.session_state.get("show_create_schedule"):

        @st.dialog("Create Schedule")
        def create_dialog():
            name = st.text_input("Name")
            if st.button("Create"):
                create_schedule(name)
                st.session_state["show_create_schedule"] = False
                st.rerun()
            if st.button("Cancel"):
                st.session_state["show_create_schedule"] = False
                st.rerun()

        create_dialog()

    if st.session_state.get("show_edit_schedule"):

        @st.dialog("Edit Schedule")
        def edit_dialog():
            name = st.text_input("Name", value=selected_name)
            if st.button("Save"):
                update_schedule(schedule_id, name)
                st.session_state["show_edit_schedule"] = False
                st.rerun()
            if st.button("Cancel"):
                st.session_state["show_edit_schedule"] = False
                st.rerun()

        edit_dialog()

    if st.session_state.get("show_delete_schedule"):

        @st.dialog("Delete Schedule")
        def delete_dialog():
            st.warning(f"Delete '{selected_name}'?")
            if st.button("Confirm"):
                delete_schedule(schedule_id)
                st.session_state["show_delete_schedule"] = False
                st.rerun()
            if st.button("Cancel"):
                st.session_state["show_delete_schedule"] = False
                st.rerun()

        delete_dialog()

    if st.session_state.get("pending_cell_shift"):
        pending = st.session_state["pending_cell_shift"]

        @st.dialog("Add Shift")
        def add_shift_dialog():
            default_start = datetime.fromisoformat(f"{pending['day_str']}T08:00:00")
            start_date = st.date_input("Date", value=default_start.date())
            start_time = st.time_input("Start time", value=default_start.time())
            duration = st.number_input("Duration (hours)", min_value=1.0, max_value=24.0, value=8.0, step=0.5)

            if st.button("Create shift", use_container_width=True):
                shift_start = datetime.combine(start_date, start_time).isoformat()
                create_shift(
                    pending["schedule_id"],
                    pending["employee_id"],
                    shift_start,
                    duration
                )
                st.session_state["pending_cell_shift"] = None
                st.rerun()

            if st.button("Cancel", use_container_width=True):
                st.session_state["pending_cell_shift"] = None
                st.rerun()

        add_shift_dialog()

    if st.session_state.get("editing_shift"):
        editing = st.session_state["editing_shift"]

        @st.dialog("Edit Shift")
        def edit_shift_dialog():
            current_start = datetime.fromisoformat(editing["start"])
            start_date = st.date_input("Date", value=current_start.date(), key=f"edit_date_{editing['id']}")
            start_time = st.time_input("Start time", value=current_start.time(), key=f"edit_time_{editing['id']}")
            duration = st.number_input(
                "Duration (hours)",
                min_value=1.0,
                max_value=24.0,
                value=float(editing["durationHours"]),
                step=0.5,
                key=f"edit_duration_{editing['id']}"
            )

            if st.button("Save changes", use_container_width=True):
                shift_start = datetime.combine(start_date, start_time).isoformat()
                update_shift(editing["id"], start=shift_start, duration=duration)
                st.session_state["editing_shift"] = None
                st.rerun()

            if st.button("Cancel", use_container_width=True):
                st.session_state["editing_shift"] = None
                st.rerun()

        edit_shift_dialog()

    if st.session_state.get("deleting_shift"):
        deleting = st.session_state["deleting_shift"]

        @st.dialog("Delete Shift")
        def delete_shift_dialog():
            start_dt = datetime.fromisoformat(deleting["start"])
            st.warning(
                f"Delete shift for {deleting['employee_name']} on "
                f"{start_dt.strftime('%b %d, %Y at %I:%M %p')}?"
            )

            if st.button("Confirm delete", use_container_width=True):
                delete_shift(deleting["id"])
                st.session_state["deleting_shift"] = None
                st.rerun()

            if st.button("Cancel", use_container_width=True):
                st.session_state["deleting_shift"] = None
                st.rerun()

        delete_shift_dialog()

    if st.session_state.get("remove_schedule_employee"):
        removal = st.session_state["remove_schedule_employee"]

        @st.dialog("Remove Employee")
        def remove_employee_dialog():
            st.warning(f"Remove {removal['employee_name']} from this schedule?")

            if st.button("Confirm remove", use_container_width=True):
                remove_employee_from_schedule(removal["schedule_id"], removal["employee_id"])
                st.session_state["remove_schedule_employee"] = None
                st.rerun()

            if st.button("Cancel", use_container_width=True):
                st.session_state["remove_schedule_employee"] = None
                st.rerun()

        remove_employee_dialog()
