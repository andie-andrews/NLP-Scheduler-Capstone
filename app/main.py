from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from ui.login import render_login
from ui.tabs import get_tabs
from ui.my_schedule import render as render_my_schedule
from ui.manage_employees import render as render_manage_employees
from ui.manage_schedules import render as render_manage_schedules
from ui.ai_assistant import render_ai_assistant as render_ai_assistant
from auth import logout
from ui.styles import apply_global_styles

st.set_page_config(page_title="Scheduler App", layout="wide")
apply_global_styles()

# 🔐 Not logged in
if "token" not in st.session_state:
    render_login()
    st.stop()
else:
    st.sidebar.markdown(
        f"""
        <div class='profile-card'>
            <div class='profile-name'>👋 {st.session_state['full_name']}</div>
            <div class='profile-role'>Role: {st.session_state['role']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 🔓 Logged in
st.sidebar.title("Navigation")
st.sidebar.caption("Choose a workspace")

if st.sidebar.button("Logout"):
    logout()
    st.rerun()

tabs = get_tabs()

selected = st.sidebar.radio("Go to", tabs)

# 🧭 Route to tab
if selected == "My Schedule":
    render_my_schedule()

elif selected == "Manage Employees":
    render_manage_employees()

elif selected == "Manage Schedules":
    render_manage_schedules()

elif selected == "AI Assistant":
    render_ai_assistant()