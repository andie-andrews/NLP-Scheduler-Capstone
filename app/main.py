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


def render_main_view(active_view: str):
    if active_view == "My Schedule":
        render_my_schedule()
    elif active_view == "Manage Employees":
        render_manage_employees()
    elif active_view == "Manage Schedules":
        render_manage_schedules()


tabs = [tab for tab in get_tabs() if tab != "AI Assistant"]
main_nav_tab = st.session_state.get("main_nav_tab", tabs[0])
if main_nav_tab not in tabs:
    main_nav_tab = tabs[0]

selected = st.sidebar.selectbox(
    "Go to",
    tabs,
    index=tabs.index(main_nav_tab),
)
st.session_state["main_nav_tab"] = selected

# --- AI panel state ---
if "ai_panel_open" not in st.session_state:
    st.session_state.ai_panel_open = True
if "ai_panel_collapsed" not in st.session_state:
    st.session_state.ai_panel_collapsed = False
if "ai_panel_width" not in st.session_state:
    st.session_state.ai_panel_width = 35

st.sidebar.markdown("##### AI Assistant")
if st.sidebar.button("🤖 Open Assistant", use_container_width=True):
    st.session_state.ai_panel_open = True
    st.session_state.ai_panel_collapsed = False

if st.session_state.ai_panel_open:
    st.sidebar.caption("Drag the center handle (↔) to resize")

# --- Render split view ---
if not st.session_state.ai_panel_open:
    render_main_view(selected)
else:
    width = 8 if st.session_state.ai_panel_collapsed else st.session_state.ai_panel_width
    left_width = max(100 - width, 25)
    handle_width = 2 if not st.session_state.ai_panel_collapsed else 1

    main_col, resize_col, assistant_col = st.columns(
        [left_width, handle_width, 100 - left_width - handle_width],
        gap="small",
    )

    with main_col:
        with st.container(key="main_scroll_pane"):
            render_main_view(selected)

    with resize_col:
        if st.session_state.ai_panel_collapsed:
            st.markdown("<div class='ai-resize-line'></div>", unsafe_allow_html=True)
        else:
            st.markdown(
                """
                <div class='ai-resize-handle' title='Drag left/right to resize'>
                    <span>↔</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with assistant_col:
        panel_controls = st.columns([7, 1, 1], gap="small")
        with panel_controls[0]:
            st.markdown("#### 🤖 AI Assistant")
        with panel_controls[1]:
            if st.button(
                "◀" if not st.session_state.ai_panel_collapsed else "▶",
                key="toggle_ai_collapse",
                help="Collapse/expand assistant panel",
                use_container_width=True,
            ):
                st.session_state.ai_panel_collapsed = not st.session_state.ai_panel_collapsed
                st.rerun()
        with panel_controls[2]:
            if st.button(
                "✕",
                key="close_ai_panel",
                help="Close assistant panel",
                use_container_width=True,
            ):
                st.session_state.ai_panel_open = False
                st.rerun()

        if st.session_state.ai_panel_collapsed:
            st.caption("Assistant collapsed. Click ▶ to expand.")
        else:
            with st.container(key="assistant_shell"):
                render_ai_assistant(embedded=True)

    st.markdown(
        """
        <style>
            .ai-resize-handle {
                width: 100%;
                height: 4.5rem;
                border-radius: 0.5rem;
                border: 1px solid rgba(120, 120, 120, 0.35);
                display: flex;
                align-items: center;
                justify-content: center;
                user-select: none;
                font-size: 1.15rem;
                background: rgba(120, 120, 120, 0.08);
            }

            .ai-resize-line {
                width: 100%;
                height: 4.5rem;
                border-left: 1px solid rgba(120, 120, 120, 0.35);
            }

            .st-key-main_scroll_pane {
                height: calc(100vh - 7rem);
                overflow-y: auto;
                overflow-x: hidden;
                padding: 0 0.1rem 1.25rem 0;
            }

            .st-key-assistant_shell {
                height: calc(100vh - 7rem);
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
