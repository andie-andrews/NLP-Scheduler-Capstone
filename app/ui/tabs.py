import streamlit as st

def get_tabs():
    tabs = ["My Schedule"]

    if st.session_state["role"] in ["Supervisor", "Manager"]:
        tabs.extend(["Manage Employees", "Manage Schedules"])

    if st.session_state["role"] == "Manager":
        tabs.append("View Schedule")

    # 👇 ADD THIS
    tabs.append("AI Assistant")

    return tabs