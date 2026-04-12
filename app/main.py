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
if "ai_panel_open" not in st.session_state:
    st.session_state["ai_panel_open"] = False
if "ai_panel_width" not in st.session_state:
    st.session_state["ai_panel_width"] = 35
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
    st.session_state["ai_panel_open"] = True
    active_view = st.session_state.get("main_nav_tab", tabs[0])

st.sidebar.markdown("##### AI Panel")
st.session_state["ai_panel_width"] = st.sidebar.slider(
    "Panel width (%)",
    min_value=25,
    max_value=55,
    value=st.session_state["ai_panel_width"],
    help="Drag to resize the AI panel and main view split.",
)
if st.sidebar.button(
    "Hide AI Panel" if st.session_state["ai_panel_open"] else "Show AI Panel",
    use_container_width=True,
):
    st.session_state["ai_panel_open"] = not st.session_state["ai_panel_open"]
    st.rerun()

st.session_state["active_tab"] = active_view

def _render_main_content(view_name: str) -> None:
    if view_name == "My Schedule":
        render_my_schedule()
    elif view_name == "Manage Employees":
        render_manage_employees()
    elif view_name == "Manage Schedules":
        render_manage_schedules()


def _inject_resizable_layout_css() -> None:
    st.markdown(
        """
        <style>
            .app-main-view {
                min-width: 0;
            }

            .assistant-resize-shell {
                resize: horizontal;
                overflow: auto;
                min-width: 280px;
                max-width: 100%;
                border-left: 1px solid #dbe7ff;
                padding-left: 0.85rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


if active_view == "AI Assistant":
    st.session_state["ai_panel_open"] = True
    active_view = st.session_state.get("main_nav_tab", tabs[0])
    st.session_state["active_tab"] = active_view

if st.session_state["ai_panel_open"]:
    _inject_resizable_layout_css()
    panel_weight = st.session_state["ai_panel_width"]
    main_weight = max(100 - panel_weight, 45)
    main_col, assistant_col = st.columns([main_weight, panel_weight], gap="small")
    with main_col:
        st.markdown('<div class="app-main-view">', unsafe_allow_html=True)
        _render_main_content(active_view)
        st.markdown("</div>", unsafe_allow_html=True)
    with assistant_col:
        st.markdown('<div class="assistant-resize-shell">', unsafe_allow_html=True)
        close_col, _ = st.columns([1, 6])
        with close_col:
            if st.button("✕", key="close_ai_panel", help="Close assistant panel"):
                st.session_state["ai_panel_open"] = False
                st.rerun()
        render_ai_assistant(embedded=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    _render_main_content(active_view)
