import streamlit as st

from ui.login import render_login
from ui.tabs import get_tabs
from ui.my_schedule import render as render_my_schedule
from ui.manage_employees import render as render_manage_employees
from ui.manage_schedules import render as render_manage_schedules
from auth import logout

st.set_page_config(page_title="Scheduler App", layout="wide")

# 🔐 Not logged in
if "token" not in st.session_state:
    render_login()
    st.stop()

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