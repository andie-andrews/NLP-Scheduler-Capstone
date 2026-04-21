import streamlit as st

def get_tabs():
    tabs = ["My Schedule"]

    if st.session_state["role"] in ["Supervisor", "Manager"]:
        tabs.extend(["Manage Employees", "Manage Schedule Groups"])

    # 👇 ADD THIS
    tabs.append("AI Assistant")

    return tabs