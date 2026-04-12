import streamlit as st

from auth import login
from ui.styles import render_page_header


def render_login():
    left, center, right = st.columns([1, 1.5, 1])

    with center:
        render_page_header(
            "Scheduler Login",
            "Sign in to access schedules, staffing, and assistant tools.",
        )
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            success = login(username, password)

            if success:
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials")

        st.markdown("</div>", unsafe_allow_html=True)
