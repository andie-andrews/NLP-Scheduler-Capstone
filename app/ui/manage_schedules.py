import streamlit as st
from api_client import (
    get_schedules,
    get_schedule_employees,
    get_schedule_shifts,
    get_my_schedule,
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
from ui.theme import render_page_header


def render():
    def rerun_app():
        try:
            st.rerun(scope="app")
        except TypeError:
            st.rerun()

    def handle_mutation(response, success_message):
        if response.status_code in (200, 201, 204):
            st.success(success_message)
            return True

        try:
            error_payload = response.json()
        except Exception:
            error_payload = response.text or "Unknown error"

        if isinstance(error_payload, dict):
            errors = error_payload.get("errors") or {}

            overlap_errors = []
            if isinstance(errors, dict):
                overlap_errors = errors.get("overlapping_shift") or []
            elif isinstance(errors, list):
                overlap_errors = [
                    item.get("message")
                    for item in errors
                    if isinstance(item, dict) and item.get("code") == "overlapping_shift"
                ]

            if overlap_errors:
                st.error("Shift not created: it overlaps an existing shift for this employee.")
                for detail in overlap_errors:
                    st.caption(detail)
                return False

        st.error(f"Request failed ({response.status_code}): {error_payload}")
        return False

    def overlaps_existing_shift(*, employee_id: int, start_iso: str, duration_hours: int, exclude_shift_id: int | None = None):
        proposed_start = datetime.fromisoformat(start_iso)
        proposed_end = proposed_start + timedelta(hours=int(duration_hours))
        window_start = (proposed_start - timedelta(days=1)).date().isoformat()
        window_end = (proposed_end + timedelta(days=1)).date().isoformat()

        shifts_response = get_my_schedule(
            employee_id,
            params={"startDate": window_start, "endDate": window_end},
        )

        if shifts_response.status_code != 200:
            return False, None

        try:
            existing_shifts = shifts_response.json() or []
        except Exception:
            return False, None

        for existing in existing_shifts:
            if exclude_shift_id and existing.get("id") == exclude_shift_id:
                continue

            existing_start = datetime.fromisoformat(existing["start"])
            existing_end = existing_start + timedelta(hours=int(existing.get("durationHours", 0)))
            if existing_start < proposed_end and existing_end > proposed_start:
                detail = (
                    f"Overlaps existing shift on {existing_start.strftime('%A, %b %d, %Y')} "
                    f"({existing_start.strftime('%I:%M %p')} - {existing_end.strftime('%I:%M %p')})."
                )
                return True, detail

        return False, None

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

    all_schedules_option = "__all_schedules__"
    toolbar_selection = st.session_state.get("manage_schedules_selected_schedule", all_schedules_option)
    disable_schedule_delete = toolbar_selection == all_schedules_option

    # 🔥 HEADER
    render_page_header("Manage Schedules", "Coordinate weekly staffing, shifts, and schedule assignments with clarity.")
    st.markdown(
        """
        <style>
            .st-key-manage_schedules_scroll_body {
                flex: 1;
                min-height: 0;
                overflow-y: auto;
                overflow-x: hidden;
                padding-right: 0.35rem;
                padding-bottom: 0.5rem;
            }

            .st-key-manage_schedules_scroll_body::-webkit-scrollbar {
                width: 10px;
            }

            .st-key-manage_schedules_scroll_body::-webkit-scrollbar-thumb {
                background: rgba(120, 120, 120, 0.45);
                border-radius: 999px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    header_col1, header_col2 = st.columns([6, 2])

    with header_col1:
        st.caption("Select a schedule and use the controls on the right to manage it.")

    with header_col2:
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        if btn_col1.button("➕", use_container_width=True):
            st.session_state["show_create_schedule"] = True

        if btn_col2.button("✎", use_container_width=True):
            st.session_state["show_edit_schedule"] = True

        if btn_col3.button("🗑️", use_container_width=True, disabled=disable_schedule_delete):
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

    schedule_name_by_id = {s["id"]: s["name"] for s in schedules}
    schedule_options_for_forms = [
        {"id": s["id"], "name": s["name"]}
        for s in schedules
    ]

    schedule_options = [all_schedules_option] + [s["id"] for s in schedules]
    selected_schedule_state = st.session_state.get("manage_schedules_selected_schedule")
    if selected_schedule_state not in schedule_options:
        st.session_state["manage_schedules_selected_schedule"] = all_schedules_option

    selected_schedule_option = st.selectbox(
        "Select Schedule",
        schedule_options,
        format_func=lambda option: "All Schedules"
        if option == all_schedules_option
        else schedule_name_by_id.get(option, f"Schedule {option}"),
        key="manage_schedules_selected_schedule",
    )

    previous_schedule_option = st.session_state.get(
        "manage_schedules_previous_schedule",
        selected_schedule_option
    )
    if previous_schedule_option != selected_schedule_option:
        st.session_state["pending_cell_shift"] = None
        st.session_state["editing_shift"] = None
        st.session_state["deleting_shift"] = None
    st.session_state["manage_schedules_previous_schedule"] = selected_schedule_option

    viewing_all_schedules = selected_schedule_option == all_schedules_option
    schedule_id = None if viewing_all_schedules else selected_schedule_option
    selected_name = "All Schedules" if viewing_all_schedules else schedule_name_by_id.get(schedule_id, "")

    if viewing_all_schedules:
        st.session_state["show_delete_schedule"] = False

    # 🔹 WEEK NAV
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

    if nav_col1.button("◀ Previous", use_container_width=True):
        st.session_state["week_offset"] -= 1

    if nav_col3.button("Next ▶", use_container_width=True):
        st.session_state["week_offset"] += 1

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    base_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    start_of_week = base_week + timedelta(weeks=st.session_state["week_offset"])
    end_of_week = start_of_week + timedelta(days=6)
    days = [start_of_week + timedelta(days=i) for i in range(7)]

    nav_col2.markdown(
        f"<div class='metric-tile' style='text-align:center;font-weight:600;'>Week of {start_of_week.strftime('%b %d, %Y')}</div>",
        unsafe_allow_html=True
    )

    with st.container(key="manage_schedules_scroll_body"):
        # 🔹 LOAD EMPLOYEES
        all_emp_res = get_all_employees()
        all_employees = all_emp_res.json() if all_emp_res.status_code == 200 else []

        if viewing_all_schedules:
            employees = all_employees
        else:
            emp_res = get_schedule_employees(schedule_id)
            employees = emp_res.json() if emp_res.status_code == 200 else []

        # 🔥 ZERO STATE
        if not employees:
            if viewing_all_schedules:
                st.info("No employees found.")
                return

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
                rerun_app()

            return

        # 🔹 LOAD SHIFTS
        if viewing_all_schedules:
            shifts = []
            for sched in schedules:
                shift_res = get_schedule_shifts(
                    sched["id"],
                    params={
                        "startDate": start_of_week.date().isoformat(),
                        "endDate": end_of_week.date().isoformat(),
                    }
                )
                if shift_res.status_code != 200:
                    continue
                schedule_shifts = shift_res.json() or []
                for shift in schedule_shifts:
                    shift["scheduleName"] = sched["name"]
                    shift["scheduleId"] = sched["id"]
                shifts.extend(schedule_shifts)
        else:
            shift_res = get_schedule_shifts(
                schedule_id,
                params={
                    "startDate": start_of_week.date().isoformat(),
                    "endDate": end_of_week.date().isoformat(),
                }
            )
            shifts = shift_res.json() if shift_res.status_code == 200 else []
            for shift in shifts:
                shift["scheduleName"] = schedule_name_by_id.get(schedule_id)
                shift["scheduleId"] = schedule_id

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
        st.markdown(
            """
            <style>
            [class*="st-key-action_cell_"] div[data-testid="stPopover"] button {
                background-color: #2f2f2f;
                border-color: #2f2f2f;
                color: #ffffff;
                font-size: 0.8rem;
                padding: 0.2rem 0.45rem;
                min-height: 1.6rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

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

            if not viewing_all_schedules and row[1].button("❌", key=f"remove_{emp['id']}"):
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

                    with st.container(key=f"action_cell_{cell_id}"):
                        with st.popover("Action"):
                            st.caption(f"{full_name} • {day.strftime('%a %m/%d')}")

                            if st.button("Add shift", key=f"cell_add_shift_{cell_id}", use_container_width=True):
                                st.session_state["pending_cell_shift"] = {
                                    "schedule_id": schedule_id,
                                    "employee_id": emp["id"],
                                    "employee_name": full_name,
                                    "day_str": day_str
                                }
                                rerun_app()

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
                                schedule_name = shift.get("scheduleName")
                                if schedule_name:
                                    st.caption(f"{full_name} • {day.strftime('%a %m/%d')} • {schedule_name}")
                                else:
                                    st.caption(f"{full_name} • {day.strftime('%a %m/%d')}")

                                if st.button("Edit shift", key=f"edit_shift_{shift_id}", use_container_width=True):
                                    st.session_state["editing_shift"] = {
                                        "id": shift_id,
                                        "schedule_id": shift.get("scheduleId"),
                                        "employee_id": emp["id"],
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

        if not viewing_all_schedules and available:

            ghost_key = f"ghost_add_{schedule_id}_{len(employees)}"

            ghost_row = st.columns(9)

            selected = ghost_row[0].selectbox(
                "Add employee",
                options=[None] + [e["id"] for e in available],
                format_func=lambda x: "➕ Add employee..." if x is None else
                next(f"{e['firstName']} {e['lastName']}" for e in available if e["id"] == x),
                key=ghost_key,
                label_visibility="collapsed",
            )

            if selected:
                add_employee_to_schedule(schedule_id, selected)
                selected = None
                rerun_app()

    # 🔥 MODALS (unchanged)

    if st.session_state.get("show_create_schedule"):

        @st.dialog("Create Schedule")
        def create_dialog():
            name = st.text_input("Name")
            if st.button("Create"):
                create_schedule(name)
                st.session_state["show_create_schedule"] = False
                rerun_app()
            if st.button("Cancel"):
                st.session_state["show_create_schedule"] = False
                rerun_app()

        create_dialog()

    if not viewing_all_schedules and st.session_state.get("show_edit_schedule"):

        @st.dialog("Edit Schedule")
        def edit_dialog():
            name = st.text_input("Name", value=selected_name)
            if st.button("Save"):
                update_schedule(schedule_id, name)
                st.session_state["show_edit_schedule"] = False
                rerun_app()
            if st.button("Cancel"):
                st.session_state["show_edit_schedule"] = False
                rerun_app()

        edit_dialog()

    if not viewing_all_schedules and st.session_state.get("show_delete_schedule"):

        @st.dialog("Delete Schedule")
        def delete_dialog():
            st.warning(f"Delete '{selected_name}'?")
            if st.button("Confirm"):
                delete_schedule(schedule_id)
                st.session_state["show_delete_schedule"] = False
                rerun_app()
            if st.button("Cancel"):
                st.session_state["show_delete_schedule"] = False
                rerun_app()

        delete_dialog()

    if st.session_state.get("pending_cell_shift"):
        pending = st.session_state["pending_cell_shift"]

        @st.dialog("Add Shift")
        def add_shift_dialog():
            default_start = datetime.fromisoformat(f"{pending['day_str']}T08:00:00")
            schedule_ids = [s["id"] for s in schedule_options_for_forms]
            selected_schedule_id = pending.get("schedule_id")
            if selected_schedule_id not in schedule_ids and schedule_ids:
                selected_schedule_id = schedule_ids[0]

            chosen_schedule_id = st.selectbox(
                "Schedule",
                options=schedule_ids,
                index=schedule_ids.index(selected_schedule_id) if selected_schedule_id in schedule_ids else 0,
                format_func=lambda x: schedule_name_by_id.get(x, f"Schedule {x}"),
                disabled=not viewing_all_schedules,
                key=f"add_shift_schedule_{pending['employee_id']}_{pending['day_str']}"
            )

            start_date = st.date_input("Date", value=default_start.date())
            start_time = st.time_input("Start time", value=default_start.time())
            duration = st.number_input("Duration (hours)", min_value=1, max_value=24, value=8, step=1)

            if st.button("Create shift", use_container_width=True):
                shift_start = datetime.combine(start_date, start_time).isoformat()
                has_overlap, overlap_detail = overlaps_existing_shift(
                    employee_id=pending["employee_id"],
                    start_iso=shift_start,
                    duration_hours=int(duration),
                )
                if has_overlap:
                    st.error("Shift not created: it overlaps an existing shift for this employee.")
                    if overlap_detail:
                        st.caption(overlap_detail)
                    return

                result = create_shift(
                    chosen_schedule_id,
                    pending["employee_id"],
                    shift_start,
                    int(duration)
                )
                if handle_mutation(result, "Shift created."):
                    st.session_state["pending_cell_shift"] = None
                    rerun_app()

            if st.button("Cancel", use_container_width=True):
                st.session_state["pending_cell_shift"] = None
                rerun_app()

        add_shift_dialog()

    if st.session_state.get("editing_shift"):
        editing = st.session_state["editing_shift"]

        @st.dialog("Edit Shift")
        def edit_shift_dialog():
            current_start = datetime.fromisoformat(editing["start"])
            schedule_ids = [s["id"] for s in schedule_options_for_forms]
            editing_schedule_id = editing.get("schedule_id")
            if editing_schedule_id not in schedule_ids and schedule_ids:
                editing_schedule_id = schedule_ids[0]

            chosen_schedule_id = st.selectbox(
                "Schedule",
                options=schedule_ids,
                index=schedule_ids.index(editing_schedule_id) if editing_schedule_id in schedule_ids else 0,
                format_func=lambda x: schedule_name_by_id.get(x, f"Schedule {x}"),
                disabled=not viewing_all_schedules,
                key=f"edit_schedule_{editing['id']}"
            )

            start_date = st.date_input("Date", value=current_start.date(), key=f"edit_date_{editing['id']}")
            start_time = st.time_input("Start time", value=current_start.time(), key=f"edit_time_{editing['id']}")
            duration = st.number_input(
                "Duration (hours)",
                min_value=1,
                max_value=24,
                value=int(editing["durationHours"]),
                step=1,
                key=f"edit_duration_{editing['id']}"
            )

            if st.button("Save changes", use_container_width=True):
                shift_start = datetime.combine(start_date, start_time).isoformat()
                has_overlap, overlap_detail = overlaps_existing_shift(
                    employee_id=editing["employee_id"],
                    start_iso=shift_start,
                    duration_hours=int(duration),
                    exclude_shift_id=editing["id"],
                )
                if has_overlap:
                    st.error("Shift not updated: it overlaps an existing shift for this employee.")
                    if overlap_detail:
                        st.caption(overlap_detail)
                    return

                if chosen_schedule_id == editing.get("schedule_id"):
                    result = update_shift(editing["id"], start=shift_start, duration=int(duration))
                    if handle_mutation(result, "Shift updated."):
                        st.session_state["editing_shift"] = None
                        rerun_app()
                else:
                    create_result = create_shift(
                        chosen_schedule_id,
                        editing["employee_id"],
                        shift_start,
                        int(duration),
                    )
                    if not handle_mutation(create_result, "Shift moved to selected schedule."):
                        return

                    delete_result = delete_shift(editing["id"])
                    if handle_mutation(delete_result, "Original shift removed."):
                        st.session_state["editing_shift"] = None
                        rerun_app()

            if st.button("Cancel", use_container_width=True):
                st.session_state["editing_shift"] = None
                rerun_app()

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
                result = delete_shift(deleting["id"])
                if handle_mutation(result, "Shift deleted."):
                    st.session_state["deleting_shift"] = None
                    rerun_app()

            if st.button("Cancel", use_container_width=True):
                st.session_state["deleting_shift"] = None
                rerun_app()

        delete_shift_dialog()

    if st.session_state.get("remove_schedule_employee"):
        removal = st.session_state["remove_schedule_employee"]

        @st.dialog("Remove Employee")
        def remove_employee_dialog():
            st.warning(f"Remove {removal['employee_name']} from this schedule?")

            if st.button("Confirm remove", use_container_width=True):
                remove_employee_from_schedule(removal["schedule_id"], removal["employee_id"])
                st.session_state["remove_schedule_employee"] = None
                rerun_app()

            if st.button("Cancel", use_container_width=True):
                st.session_state["remove_schedule_employee"] = None
                rerun_app()

        remove_employee_dialog()
