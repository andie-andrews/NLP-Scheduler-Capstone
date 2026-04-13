import streamlit as st
from collections import defaultdict
from datetime import datetime, timedelta

from api_client import (
    create_shift,
    delete_shift,
    get_all_employees,
    get_my_schedule,
    get_schedule_shifts,
    get_schedules,
    update_shift,
)
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
                st.error("Shift not saved: it overlaps an existing shift for this employee.")
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

    if "view_schedule_week_offset" not in st.session_state:
        st.session_state["view_schedule_week_offset"] = 0
    if "view_schedule_pending_cell_shift" not in st.session_state:
        st.session_state["view_schedule_pending_cell_shift"] = None
    if "view_schedule_editing_shift" not in st.session_state:
        st.session_state["view_schedule_editing_shift"] = None
    if "view_schedule_deleting_shift" not in st.session_state:
        st.session_state["view_schedule_deleting_shift"] = None

    render_page_header("View Schedule", "See weekly shifts across all schedules and employees in a single planner.")

    schedules_res = get_schedules()
    if schedules_res.status_code != 200:
        st.error("Failed to load schedules")
        return

    employees_res = get_all_employees()
    if employees_res.status_code != 200:
        st.error("Failed to load employees")
        return

    schedules = schedules_res.json() or []
    employees = employees_res.json() or []

    if not schedules:
        st.info("No schedules available")
        return

    if not employees:
        st.info("No employees available")
        return

    schedule_filter_options = ["All schedules"] + [s["name"] for s in schedules]
    selected_schedule_filter = st.selectbox("Filter by schedule", schedule_filter_options)

    employee_filter_options = ["All employees"] + [f"{e['firstName']} {e['lastName']}" for e in employees]
    selected_employee_filter = st.selectbox("Filter by employee", employee_filter_options)

    if selected_schedule_filter == "All schedules":
        filtered_schedules = schedules
    else:
        filtered_schedules = [s for s in schedules if s["name"] == selected_schedule_filter]

    schedule_lookup = {s["id"]: s["name"] for s in schedules}

    employee_lookup = {e["id"]: f"{e['firstName']} {e['lastName']}" for e in employees}

    if selected_employee_filter == "All employees":
        filtered_employees = employees
    else:
        filtered_employees = [
            e for e in employees if f"{e['firstName']} {e['lastName']}" == selected_employee_filter
        ]

    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

    if nav_col1.button("◀ Previous", use_container_width=True):
        st.session_state["view_schedule_week_offset"] -= 1

    if nav_col3.button("Next ▶", use_container_width=True):
        st.session_state["view_schedule_week_offset"] += 1

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    base_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    start_of_week = base_week + timedelta(weeks=st.session_state["view_schedule_week_offset"])
    end_of_week = start_of_week + timedelta(days=6)
    days = [start_of_week + timedelta(days=i) for i in range(7)]

    nav_col2.markdown(
        f"<div class='metric-tile' style='text-align:center;font-weight:600;'>Week of {start_of_week.strftime('%b %d, %Y')}</div>",
        unsafe_allow_html=True,
    )

    all_shifts = []
    shift_query_params = {
        "startDate": start_of_week.date().isoformat(),
        "endDate": end_of_week.date().isoformat(),
    }

    for schedule in filtered_schedules:
        shift_res = get_schedule_shifts(schedule["id"], params=shift_query_params)
        if shift_res.status_code != 200:
            continue

        for shift in shift_res.json() or []:
            shift["scheduleName"] = schedule["name"]
            all_shifts.append(shift)

    shift_lookup = defaultdict(list)
    for shift in all_shifts:
        date_key = shift["start"][:10]
        shift_lookup[(shift["employeeId"], date_key)].append(shift)

    header = st.columns(8)
    header[0].markdown("**Employee**")

    for i, day in enumerate(days):
        header[i + 1].markdown(
            f"<div style='text-align:center'>{day.strftime('%a %m/%d')}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    day_totals = defaultdict(int)

    for emp in filtered_employees:
        emp_name = employee_lookup[emp["id"]]
        employee_total = 0

        for day in days:
            key = (emp["id"], day.strftime("%Y-%m-%d"))
            for shift in shift_lookup.get(key, []):
                employee_total += int(shift.get("durationHours", 0))
                day_totals[day.strftime("%Y-%m-%d")] += int(shift.get("durationHours", 0))

        row = st.columns(8)
        row[0].markdown(f"**{emp_name} ({employee_total}h)**")

        for i, day in enumerate(days):
            day_str = day.strftime("%Y-%m-%d")
            key = (emp["id"], day_str)

            with row[i + 1]:
                cell_id = f"view_{emp['id']}_{day_str}"

                with st.popover("Add", use_container_width=True):
                    st.caption(f"{emp_name} • {day.strftime('%a %m/%d')}")
                    if st.button("Add shift", key=f"view_cell_add_shift_{cell_id}", use_container_width=True):
                        st.session_state["view_schedule_pending_cell_shift"] = {
                            "employee_id": emp["id"],
                            "employee_name": emp_name,
                            "day_str": day_str,
                            "default_schedule_id": filtered_schedules[0]["id"] if len(filtered_schedules) == 1 else None,
                        }
                        rerun_app()

                for shift in shift_lookup.get(key, []):
                    start_dt = datetime.fromisoformat(shift["start"])
                    end_dt = start_dt + timedelta(hours=int(shift["durationHours"]))
                    shift_id = shift["id"]
                    schedule_name = schedule_lookup.get(shift["scheduleId"], shift.get("scheduleName", "Unknown"))
                    shift_label = (
                        f"[{schedule_name}] {start_dt.strftime('%I:%M %p')} - "
                        f"{end_dt.strftime('%I:%M %p')} ({shift['durationHours']}h)"
                    )

                    with st.popover(shift_label, use_container_width=True):
                        st.caption(f"{emp_name} • {schedule_name}")

                        if st.button("Edit shift", key=f"view_edit_shift_{shift_id}", use_container_width=True):
                            st.session_state["view_schedule_editing_shift"] = {
                                "id": shift_id,
                                "employee_id": shift["employeeId"],
                                "employee_name": emp_name,
                                "schedule_id": shift["scheduleId"],
                                "schedule_name": schedule_name,
                                "start": shift["start"],
                                "durationHours": shift["durationHours"],
                            }
                            rerun_app()

                        if st.button("Delete shift", key=f"view_delete_shift_{shift_id}", use_container_width=True):
                            st.session_state["view_schedule_deleting_shift"] = {
                                "id": shift_id,
                                "employee_name": emp_name,
                                "start": shift["start"],
                            }
                            rerun_app()

    st.markdown("---")
    footer = st.columns(8)
    footer[0].markdown("Totals")
    for i, day in enumerate(days):
        footer[i + 1].markdown(f"**{day_totals[day.strftime('%Y-%m-%d')]}h**")

    if st.session_state.get("view_schedule_pending_cell_shift"):
        pending = st.session_state["view_schedule_pending_cell_shift"]

        @st.dialog("Add Shift")
        def add_shift_dialog():
            default_start = datetime.fromisoformat(f"{pending['day_str']}T08:00:00")
            start_date = st.date_input("Date", value=default_start.date())
            start_time = st.time_input("Start time", value=default_start.time())
            duration = st.number_input("Duration (hours)", min_value=1, max_value=24, value=8, step=1)

            sched_options = {s["name"]: s["id"] for s in schedules}
            default_index = 0
            if pending.get("default_schedule_id"):
                default_index = list(sched_options.values()).index(pending["default_schedule_id"])

            selected_schedule_name = st.selectbox(
                "Schedule",
                options=list(sched_options.keys()),
                index=default_index,
            )
            selected_schedule_id = sched_options[selected_schedule_name]

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
                    selected_schedule_id,
                    pending["employee_id"],
                    shift_start,
                    int(duration),
                )
                if handle_mutation(result, "Shift created."):
                    st.session_state["view_schedule_pending_cell_shift"] = None
                    rerun_app()

            if st.button("Cancel", use_container_width=True):
                st.session_state["view_schedule_pending_cell_shift"] = None
                rerun_app()

        add_shift_dialog()

    if st.session_state.get("view_schedule_editing_shift"):
        editing = st.session_state["view_schedule_editing_shift"]

        @st.dialog("Edit Shift")
        def edit_shift_dialog():
            current_start = datetime.fromisoformat(editing["start"])
            start_date = st.date_input("Date", value=current_start.date(), key=f"view_edit_date_{editing['id']}")
            start_time = st.time_input("Start time", value=current_start.time(), key=f"view_edit_time_{editing['id']}")
            duration = st.number_input(
                "Duration (hours)",
                min_value=1,
                max_value=24,
                value=int(editing["durationHours"]),
                step=1,
                key=f"view_edit_duration_{editing['id']}",
            )

            sched_options = {s["name"]: s["id"] for s in schedules}
            schedule_names = list(sched_options.keys())
            schedule_ids = list(sched_options.values())
            try:
                default_index = schedule_ids.index(editing["schedule_id"])
            except ValueError:
                default_index = 0

            selected_schedule_name = st.selectbox(
                "Schedule",
                options=schedule_names,
                index=default_index,
                key=f"view_edit_schedule_{editing['id']}",
            )
            selected_schedule_id = sched_options[selected_schedule_name]

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

                if selected_schedule_id == editing["schedule_id"]:
                    result = update_shift(editing["id"], start=shift_start, duration=int(duration))
                    if handle_mutation(result, "Shift updated."):
                        st.session_state["view_schedule_editing_shift"] = None
                        rerun_app()
                    return

                delete_result = delete_shift(editing["id"])
                if not handle_mutation(delete_result, "Original shift removed."):
                    return

                create_result = create_shift(
                    selected_schedule_id,
                    editing["employee_id"],
                    shift_start,
                    int(duration),
                )
                if handle_mutation(create_result, "Shift updated."):
                    st.session_state["view_schedule_editing_shift"] = None
                    rerun_app()

            if st.button("Cancel", use_container_width=True):
                st.session_state["view_schedule_editing_shift"] = None
                rerun_app()

        edit_shift_dialog()

    if st.session_state.get("view_schedule_deleting_shift"):
        deleting = st.session_state["view_schedule_deleting_shift"]

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
                    st.session_state["view_schedule_deleting_shift"] = None
                    rerun_app()

            if st.button("Cancel", use_container_width=True):
                st.session_state["view_schedule_deleting_shift"] = None
                rerun_app()

        delete_shift_dialog()
