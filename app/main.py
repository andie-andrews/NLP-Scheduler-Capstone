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
    f"""
    <div class='sidebar-user'>
        <div class='sidebar-muted'>Signed in as</div>
        <div><b>{st.session_state['full_name']}</b></div>
        <div style='height:0.35rem;'></div>
        <div class='sidebar-muted'>Role</div>
        <div><b>{st.session_state['role']}</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.subheader("Navigation")

if st.sidebar.button("Logout", use_container_width=True):
    logout()
    st.rerun()

tabs = [tab for tab in get_tabs() if tab != "AI Assistant"]
active_view = st.session_state.get("active_tab", tabs[0])
main_nav_tab = st.session_state.get("main_nav_tab", tabs[0])
if main_nav_tab not in tabs:
    main_nav_tab = tabs[0]

selected = st.sidebar.selectbox(
    "Go to",
    tabs,
    index=tabs.index(main_nav_tab),
)
st.session_state["main_nav_tab"] = selected

if selected != main_nav_tab:
    active_view = selected
elif active_view != "AI Assistant":
    active_view = selected

st.sidebar.markdown("##### Quick Access")
if st.sidebar.button("🤖 AI Assistant", use_container_width=True):
    active_view = "AI Assistant"

st.session_state["active_tab"] = active_view

if active_view == "My Schedule":
    render_my_schedule()
elif active_view == "Manage Employees":
    render_manage_employees()
elif active_view == "Manage Schedules":
    render_manage_schedules()
elif active_view == "AI Assistant":
    render_ai_assistant()
