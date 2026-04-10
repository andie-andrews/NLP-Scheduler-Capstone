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

def post(path, data = None):
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

def get_my_schedule(employee_id, params=None):
    return get(f"/api/employees/{employee_id}/shifts", params=params)

def get_schedules():
    return get("/api/schedules")

def get_schedule_employees(schedule_id):
    return get(f"/api/schedules/{schedule_id}/scheduleEmployees")

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

# -------------------------------
# SCHEDULE EMPLOYEES
# -------------------------------

def add_employee_to_schedule(schedule_id, employee_id):
    return post(
        f"/api/schedules/{schedule_id}/scheduleEmployees/{employee_id}"
    )


def remove_employee_from_schedule(schedule_id, employee_id):
    return requests.delete(
        f"{BASE_URL}/api/schedules/{schedule_id}/scheduleEmployees/{employee_id}",
        headers=get_headers(),
        verify=False
    )


# -------------------------------
# EMPLOYEE CRUD
# -------------------------------

def get_all_employees(params=None):
    return get("/api/employees", params=params)


def get_employee(employee_id):
    return get(f"/api/employees/{employee_id}")


def create_employee(first_name, last_name, role_id=1):
    return post(
        "/api/employees",
        {
            "firstName": first_name,
            "lastName": last_name,
            "roleId": role_id
        }
    )


def update_employee(employee_id, first_name, last_name, role_id=None):
    payload = {
        "firstName": first_name,
        "lastName": last_name
    }

    if role_id is not None:
        payload["roleId"] = role_id

    return requests.put(
        f"{BASE_URL}/api/employees/{employee_id}",
        json=payload,
        headers=get_headers(),
        verify=False
    )


def delete_employee(employee_id):
    return requests.delete(
        f"{BASE_URL}/api/employees/{employee_id}",
        headers=get_headers(),
        verify=False
    )
