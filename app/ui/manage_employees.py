import streamlit as st
from api_client import (
    get_all_employees,
    create_employee,
    update_employee,
    delete_employee,
)

ROLE_OPTIONS = {
    "Employee": 1,
    "Supervisor": 2,
}

ROLE_LABELS = {value: key for key, value in ROLE_OPTIONS.items()}


def _employee_label(employee):
    role_name = ROLE_LABELS.get(employee.get("roleId"), f"Role {employee.get('roleId', '?')}")
    return f"{employee['firstName']} {employee['lastName']} ({role_name})"


def render():
    st.subheader("Manage Employees")

    if "show_create_employee" not in st.session_state:
        st.session_state["show_create_employee"] = False
    if "show_edit_employee" not in st.session_state:
        st.session_state["show_edit_employee"] = False
    if "show_delete_employee" not in st.session_state:
        st.session_state["show_delete_employee"] = False

    header_left, header_right = st.columns([5, 2])

    with header_right:
        create_col, edit_col, delete_col = st.columns(3)
        if create_col.button("➕", use_container_width=True):
            st.session_state["show_create_employee"] = True
        if edit_col.button("✎", use_container_width=True):
            st.session_state["show_edit_employee"] = True
        if delete_col.button("🗑️", use_container_width=True):
            st.session_state["show_delete_employee"] = True

    query = header_left.text_input(
        "Search employees",
        placeholder="Type first name, last name, or full name",
    ).strip()

    employees_response = get_all_employees(params={"query": query} if query else None)

    if employees_response.status_code == 403:
        st.warning("You do not have permission to manage employees.")
        return

    if employees_response.status_code != 200:
        st.error(f"Failed to load employees ({employees_response.status_code}).")
        return

    employees = employees_response.json()

    if not employees:
        st.info("No employees found.")
    else:
        st.markdown("### Employee Directory")

        for employee in employees:
            role_name = ROLE_LABELS.get(employee.get("roleId"), f"Role {employee.get('roleId', '?')}")
            cols = st.columns([1, 3, 3, 2])
            cols[0].markdown(f"`#{employee['id']}`")
            cols[1].markdown(employee["firstName"])
            cols[2].markdown(employee["lastName"])
            cols[3].markdown(role_name)

    if st.session_state.get("show_create_employee"):

        @st.dialog("Create Employee")
        def create_dialog():
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            role_name = st.selectbox("Role", list(ROLE_OPTIONS.keys()))

            submit_col, cancel_col = st.columns(2)
            if submit_col.button("Create", use_container_width=True):
                if not first_name.strip() or not last_name.strip():
                    st.error("First and last name are required.")
                    return

                res = create_employee(
                    first_name.strip(),
                    last_name.strip(),
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
            role_name = st.selectbox(
                "Role",
                list(ROLE_OPTIONS.keys()),
                index=list(ROLE_OPTIONS.values()).index(selected_employee.get("roleId", 1))
                if selected_employee.get("roleId", 1) in ROLE_OPTIONS.values()
                else 0,
            )

            submit_col, cancel_col = st.columns(2)

            if submit_col.button("Save", use_container_width=True):
                if not first_name.strip() or not last_name.strip():
                    st.error("First and last name are required.")
                    return

                res = update_employee(
                    selected_employee["id"],
                    first_name.strip(),
                    last_name.strip(),
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
