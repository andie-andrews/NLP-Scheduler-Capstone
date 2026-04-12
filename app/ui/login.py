import streamlit as st
from auth import login
from ui.theme import render_page_header


def render_login():
    render_page_header(
        "Welcome to Scheduler Pro",
        "Sign in to manage shifts, team schedules, and AI-assisted planning.",
    )

    left, center, right = st.columns([1, 1.2, 1])

    with center:
        st.markdown("<div class='app-shell'>", unsafe_allow_html=True)
        st.subheader("Sign in")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            success = login(username, password)
            if success:
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Invalid credentials.")

        st.caption("Tip: Use your manager or employee account credentials provided by your administrator.")
        st.markdown("</div>", unsafe_allow_html=True)
