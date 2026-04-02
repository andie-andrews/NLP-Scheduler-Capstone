import requests
import streamlit as st

BASE_URL = "https://localhost:7259"

def get_headers():
    token = st.session_state.get("token")
    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }

def post(path, data):
    return requests.post(
        f"{BASE_URL}{path}",
        json=data,
        headers=get_headers(),
        verify=False  # dev only
    )

def get(path, params=None):
    return requests.get(
        f"{BASE_URL}{path}",
        headers=get_headers(),
        params=params,
        verify=False
    )

def get_my_schedule():
    return get("/api/schedules/my")