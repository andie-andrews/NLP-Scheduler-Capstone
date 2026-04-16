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
role = str(st.session_state.get("role", "")).strip().lower()
if role == "employee":
    sidebar_user_role_class = "sidebar-user--employee"
elif role == "supervisor":
    sidebar_user_role_class = "sidebar-user--supervisor"
else:
    sidebar_user_role_class = "sidebar-user--default"

st.sidebar.markdown("<div class='sidebar-brand'>📅 Scheduler Pro</div>", unsafe_allow_html=True)
st.sidebar.markdown(
    f"""
    <div class='sidebar-user {sidebar_user_role_class}'>
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


def render_main_view(active_view: str):
    if active_view == "My Schedule":
        render_my_schedule()
    elif active_view == "Manage Employees":
        render_manage_employees()
    elif active_view == "Manage Schedules":
        render_manage_schedules()
    elif active_view == "AI Assistant":
        render_ai_assistant()


main_tabs = [tab for tab in get_tabs() if tab != "AI Assistant"]
main_nav_tab = st.session_state.get("main_nav_tab", main_tabs[0])
if main_nav_tab not in main_tabs:
    main_nav_tab = main_tabs[0]

if "active_view" not in st.session_state:
    st.session_state.active_view = main_nav_tab

if st.session_state.active_view != "AI Assistant":
    selected = st.sidebar.selectbox(
        "Go to",
        main_tabs,
        index=main_tabs.index(main_nav_tab),
    )
    st.session_state["main_nav_tab"] = selected
    # Keep the selected main tab in sync unless the assistant is currently active.
    st.session_state.active_view = selected

st.sidebar.markdown("##### AI Assistant")
if st.sidebar.button("🤖 Open AI Assistant", use_container_width=True):
    st.session_state.active_view = "AI Assistant"
    st.rerun()

if st.session_state.active_view == "AI Assistant":
    if st.sidebar.button("← Back to navigation", use_container_width=True):
        st.session_state.active_view = st.session_state.get("main_nav_tab", main_tabs[0])
        st.rerun()

render_main_view(st.session_state.active_view)
