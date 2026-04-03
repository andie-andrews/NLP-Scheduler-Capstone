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

def get_schedules():
    return get("/api/schedules")

def get_schedule_employees(schedule_id):
    return get(f"/api/schedules/{schedule_id}/employees")

def get_schedule_shifts(schedule_id, params=None):
    return get(f"/api/schedules/{schedule_id}/shifts", params=params)

def create_shift(schedule_id, employee_id, start, duration):
    return post(
        f"/api/schedules/{schedule_id}/shifts",
        {
            "employeeId": employee_id,
            "start": start,
            "durationHours": duration
        }
    )

# -------------------------------
# SCHEDULE CRUD
# -------------------------------

def create_schedule(name):
    return post(
        "/api/schedules",
        {
            "name": name
        }
    )


def update_schedule(schedule_id, name):
    return requests.put(
        f"{BASE_URL}/api/schedules/{schedule_id}",
        json={"name": name},
        headers=get_headers(),
        verify=False
    )


def delete_schedule(schedule_id):
    return requests.delete(
        f"{BASE_URL}/api/schedules/{schedule_id}",
        headers=get_headers(),
        verify=False
    )