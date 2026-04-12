import streamlit as st

from api_client import (
    create_employee,
    delete_employee,
    get_all_employees,
    update_employee,
)
from ui.styles import render_page_header

ROLE_OPTIONS = {
    "Employee": 1,
    "Supervisor": 2,
}

ROLE_LABELS = {value: key for key, value in ROLE_OPTIONS.items()}


def _employee_label(employee):
    role_name = ROLE_LABELS.get(employee.get("roleId"), f"Role {employee.get('roleId', '?')}")
    return f"{employee['firstName']} {employee['lastName']} - {employee['email']} ({role_name})"


def render():
    render_page_header("Manage Employees", "Search, review, and maintain employee records.")

    if "show_create_employee" not in st.session_state:
        st.session_state["show_create_employee"] = False
    if "show_edit_employee" not in st.session_state:
        st.session_state["show_edit_employee"] = False
    if "show_delete_employee" not in st.session_state:
        st.session_state["show_delete_employee"] = False

    header_left, header_right = st.columns([5, 2])

    with header_right:
        create_col, edit_col, delete_col = st.columns(3)
        if create_col.button("➕", use_container_width=True, help="Create employee"):
            st.session_state["show_create_employee"] = True
        if edit_col.button("✎", use_container_width=True, help="Edit employee"):
            st.session_state["show_edit_employee"] = True
        if delete_col.button("🗑️", use_container_width=True, help="Delete employee"):
            st.session_state["show_delete_employee"] = True

    query = header_left.text_input(
        "Search employees",
        placeholder="Type first name, last name, full name, or email",
    ).strip()

    employees_response = get_all_employees(params={"query": query} if query else None)

    if employees_response.status_code == 403:
        st.warning("You do not have permission to manage employees.")
        return

    if employees_response.status_code != 200:
        st.error(f"Failed to load employees ({employees_response.status_code}).")
        return

    employees = employees_response.json()

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Total Employees", len(employees))
    metric_col2.metric(
        "Supervisors",
        sum(1 for employee in employees if employee.get("roleId") == ROLE_OPTIONS["Supervisor"]),
    )

    if not employees:
        st.info("No employees found.")
    else:
        st.markdown("### Employee Directory")
        table_rows = [
            {
                "ID": employee["id"],
                "First Name": employee["firstName"],
                "Last Name": employee["lastName"],
                "Email": employee["email"],
                "Role": ROLE_LABELS.get(employee.get("roleId"), f"Role {employee.get('roleId', '?')}"),
            }
            for employee in employees
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

    if st.session_state.get("show_create_employee"):

        @st.dialog("Create Employee")
        def create_dialog():
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email")
            role_name = st.selectbox("Role", list(ROLE_OPTIONS.keys()))

            submit_col, cancel_col = st.columns(2)
            if submit_col.button("Create", use_container_width=True):
                if not first_name.strip() or not last_name.strip() or not email.strip():
                    st.error("First name, last name, and email are required.")
                    return

                res = create_employee(
                    first_name.strip(),
                    last_name.strip(),
                    email.strip(),
                    ROLE_OPTIONS[role_name],
                )

                if res.status_code == 201:
                    st.session_state["show_create_employee"] = False
                    st.success("Employee created.")
                    st.rerun()
                else:
                    st.error(f"Failed to create employee ({res.status_code}).")

            if cancel_col.button("Cancel", use_container_width=True):
                st.session_state["show_create_employee"] = False
                st.rerun()

        create_dialog()

    if st.session_state.get("show_edit_employee"):

        @st.dialog("Edit Employee")
        def edit_dialog():
            if not employees:
                st.info("No employees to edit.")
                if st.button("Close"):
                    st.session_state["show_edit_employee"] = False
                    st.rerun()
                return

            employee_map = {_employee_label(employee): employee for employee in employees}
            selected_label = st.selectbox("Select employee", list(employee_map.keys()))
            selected_employee = employee_map[selected_label]

            first_name = st.text_input("First Name", value=selected_employee["firstName"])
            last_name = st.text_input("Last Name", value=selected_employee["lastName"])
            email = st.text_input("Email", value=selected_employee["email"])
            role_name = st.selectbox(
                "Role",
                list(ROLE_OPTIONS.keys()),
                index=list(ROLE_OPTIONS.values()).index(selected_employee.get("roleId", 1))
                if selected_employee.get("roleId", 1) in ROLE_OPTIONS.values()
                else 0,
            )

            submit_col, cancel_col = st.columns(2)

            if submit_col.button("Save", use_container_width=True):
                if not first_name.strip() or not last_name.strip() or not email.strip():
                    st.error("First name, last name, and email are required.")
                    return

                res = update_employee(
                    selected_employee["id"],
                    first_name.strip(),
                    last_name.strip(),
                    email.strip(),
                    ROLE_OPTIONS[role_name],
                )

                if res.status_code == 204:
                    st.session_state["show_edit_employee"] = False
                    st.success("Employee updated.")
                    st.rerun()
                elif res.status_code == 404:
                    st.error("Employee no longer exists.")
                else:
                    st.error(f"Failed to update employee ({res.status_code}).")

            if cancel_col.button("Cancel", use_container_width=True):
                st.session_state["show_edit_employee"] = False
                st.rerun()

        edit_dialog()

    if st.session_state.get("show_delete_employee"):

        @st.dialog("Delete Employee")
        def delete_dialog():
            if not employees:
                st.info("No employees to delete.")
                if st.button("Close"):
                    st.session_state["show_delete_employee"] = False
                    st.rerun()
                return

            employee_map = {_employee_label(employee): employee for employee in employees}
            selected_label = st.selectbox("Select employee", list(employee_map.keys()))
            selected_employee = employee_map[selected_label]

            st.warning(
                f"Delete {selected_employee['firstName']} {selected_employee['lastName']}? This cannot be undone."
            )

            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Confirm Delete", use_container_width=True):
                res = delete_employee(selected_employee["id"])

                if res.status_code == 204:
                    st.session_state["show_delete_employee"] = False
                    st.success("Employee deleted.")
                    st.rerun()
                elif res.status_code == 404:
                    st.error("Employee no longer exists.")
                else:
                    st.error(f"Failed to delete employee ({res.status_code}).")

            if cancel_col.button("Cancel", use_container_width=True):
                st.session_state["show_delete_employee"] = False
                st.rerun()

        delete_dialog()
