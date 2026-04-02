import streamlit as st
import jwt
from api_client import post

def login(username, password):
    res = post("/api/auth/login", {
        "username": username,
        "password": password
    })

    if res.status_code == 200:
        token = res.json()["token"]

        # 🔥 Decode WITHOUT verifying signature (frontend only)
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Store raw token
        st.session_state["token"] = token

        # Extract claims
        st.session_state["employee_id"] = int(decoded.get("employeeId"))
        st.session_state["role"] = decoded.get("role")
        st.session_state["full_name"] = decoded.get("fullName")
        st.session_state["first_name"] = decoded.get("firstName")
        st.session_state["last_name"] = decoded.get("lastName")

        return True

    return False


def logout():
    st.session_state.clear()