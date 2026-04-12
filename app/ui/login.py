import streamlit as st
from auth import login


def render_login():
    st.markdown(
        """
        <style>
            .login-card {
                max-width: 460px;
                margin: 2rem auto;
                padding: 1.5rem;
                border-radius: 1rem;
                border: 1px solid rgba(49,51,63,0.2);
                background: rgba(255,255,255,0.02);
            }
            .login-card h2 {
                margin: 0 0 0.35rem;
            }
            .login-card p {
                margin: 0;
                color: rgb(115, 118, 132);
            }
        </style>
        <div class='login-card'>
            <h2>Scheduler Login</h2>
            <p>Sign in to view your shifts and manage team schedules.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input("Username", placeholder="Enter username")
    password = st.text_input("Password", type="password", placeholder="Enter password")

    if st.button("Login", use_container_width=True):
        success = login(username, password)

        if success:
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid credentials")
