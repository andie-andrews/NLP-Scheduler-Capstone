import streamlit as st
from auth import login

def render_login():
    st.title("Scheduler Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success = login(username, password)

        if success:
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid credentials")