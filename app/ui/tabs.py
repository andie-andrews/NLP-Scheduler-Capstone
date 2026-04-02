import streamlit as st

def get_tabs():
    role = st.session_state.get("role")

    tabs = ["My Schedule"]

    if role == "Supervisor":
        tabs.extend(["Manage Employees", "Manage Schedules"])

    return tabs