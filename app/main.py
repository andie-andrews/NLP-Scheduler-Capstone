from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from ui.login import render_login
from ui.tabs import get_tabs
from ui.my_schedule import render as render_my_schedule
from ui.manage_employees import render as render_manage_employees
from ui.manage_schedules import render as render_manage_schedules
from ui.ai_assistant import render_ai_assistant as render_ai_assistant
from ui.theme import inject_global_styles
from auth import logout

st.set_page_config(page_title="Scheduler App", layout="wide")
inject_global_styles()

# 🔐 Not logged in
if "token" not in st.session_state:
    render_login()
    st.stop()

# 🔓 Logged in
st.sidebar.markdown("<div class='sidebar-brand'>📅 Scheduler Pro</div>", unsafe_allow_html=True)
st.sidebar.markdown(
    f"<div class='sidebar-muted'>Signed in as</div><div><b>{st.session_state['full_name']}</b></div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<div class='sidebar-muted'>Role</div><div><b>{st.session_state['role']}</b></div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")

if st.sidebar.button("Logout", use_container_width=True):
    logout()
    st.rerun()

tabs = get_tabs()
selected = st.sidebar.radio("Go to", tabs)

if selected == "My Schedule":
    render_my_schedule()
elif selected == "Manage Employees":
    render_manage_employees()
elif selected == "Manage Schedules":
    render_manage_schedules()
elif selected == "AI Assistant":
    render_ai_assistant()
