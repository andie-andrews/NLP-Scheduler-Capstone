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

st.set_page_config(page_title="Scheduler App", layout="wide")


def _inject_global_styles():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.25rem;
            }
            [data-testid="stSidebar"] {
                border-right: 1px solid rgba(49, 51, 63, 0.2);
            }
            .app-shell {
                border: 1px solid rgba(49, 51, 63, 0.15);
                border-radius: 0.9rem;
                padding: 0.9rem 1rem;
                background: rgba(255,255,255,0.02);
                margin-bottom: 1rem;
            }
            .app-shell h1 {
                margin: 0;
                font-size: 1.35rem;
            }
            .app-shell p {
                margin: 0.2rem 0 0;
                color: rgb(115, 118, 132);
                font-size: 0.95rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_global_styles()

# 🔐 Not logged in
if "token" not in st.session_state:
    render_login()
    st.stop()
else:
    st.sidebar.success(f"Welcome, {st.session_state['full_name']}")
    st.sidebar.caption(f"Role: {st.session_state['role']}")

st.markdown(
    f"""
    <div class='app-shell'>
        <h1>Workforce Scheduler</h1>
        <p>Manage shifts, schedules, and staffing from a single workspace.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# 🔓 Logged in
st.sidebar.title("Navigation")

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
