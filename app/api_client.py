import os

import requests
import streamlit as st
import urllib3


def _runtime_environment() -> str:
    for env_var in ("SCHEDULER_RUNTIME_ENV", "APP_ENV", "ASPNETCORE_ENVIRONMENT", "ENVIRONMENT"):
        env_value = os.getenv(env_var)
        if env_value and env_value.strip():
            return env_value.strip().lower()
    return "development"


def _default_scheduler_base_url() -> str:
    if _runtime_environment() in {"production", "prod"}:
        return "https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net"
    return "http://localhost/schedulerapi"


def _default_employee_base_url() -> str:
    if _runtime_environment() in {"production", "prod"}:
        return "https://nlp-employee-api.azurewebsites.net"
    return "http://localhost/employeeapi"


SCHEDULER_BASE_URL = os.getenv("SCHEDULER_API_BASE_URL", _default_scheduler_base_url()).rstrip("/")
EMPLOYEE_BASE_URL = os.getenv("EMPLOYEE_API_BASE_URL", _default_employee_base_url()).rstrip("/")
VERIFY_SSL = os.getenv("SCHEDULER_API_VERIFY_SSL", "true").lower() == "true"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("SCHEDULER_API_TIMEOUT_SECONDS", "20"))

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_headers():
    token = st.session_state.get("token")
    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }


def _request(method: str, base_url: str, path: str, *, params=None, data=None):
    return requests.request(
        method,
        f"{base_url}{path}",
        json=data,
        headers=get_headers(),
        params=params,
        verify=VERIFY_SSL,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def post(path, data=None):
    return _request("POST", SCHEDULER_BASE_URL, path, data=data)


def get(path, params=None):
    return _request("GET", SCHEDULER_BASE_URL, path, params=params)


def _get_employee_api(path, params=None):
    return _request("GET", EMPLOYEE_BASE_URL, path, params=params)


def _post_employee_api(path, data=None):
    return _request("POST", EMPLOYEE_BASE_URL, path, data=data)


def _put_employee_api(path, data=None):
    return _request("PUT", EMPLOYEE_BASE_URL, path, data=data)


def _delete_employee_api(path):
    return _request("DELETE", EMPLOYEE_BASE_URL, path)


def get_my_schedule(employee_id, params=None):
    return _get_employee_api(f"/api/employees/{employee_id}/shifts", params=params)


def get_schedules():
    return get("/api/schedule-groups")


def get_schedule_employees(schedule_id):
    return get(f"/api/schedule-groups/{schedule_id}/scheduleGroupEmployees")


def get_schedule_shifts(schedule_id, params=None):
    return get(f"/api/schedule-groups/{schedule_id}/shifts", params=params)


def get_employee_schedules(employee_id):
    return _get_employee_api(f"/api/employees/{employee_id}/employeeScheduleGroups")


def create_shift(schedule_id, employee_id, start, duration):
    return post(
        f"/api/schedule-groups/{schedule_id}/shifts",
        {
            "employeeId": employee_id,
            "start": start,
            "durationHours": duration
        }
    )


def update_shift(shift_id, start=None, duration=None):
    payload = {}

    if start is not None:
        payload["start"] = start
    if duration is not None:
        payload["durationHours"] = duration

    return _request("PUT", SCHEDULER_BASE_URL, f"/api/shifts/{shift_id}", data=payload)


def delete_shift(shift_id):
    return _request("DELETE", SCHEDULER_BASE_URL, f"/api/shifts/{shift_id}")


# -------------------------------
# SCHEDULE CRUD
# -------------------------------

def create_schedule(name):
    return post(
        "/api/schedule-groups",
        {
            "name": name
        }
    )


def update_schedule(schedule_id, name):
    return _request("PUT", SCHEDULER_BASE_URL, f"/api/schedule-groups/{schedule_id}", data={"name": name})


def delete_schedule(schedule_id):
    return _request("DELETE", SCHEDULER_BASE_URL, f"/api/schedule-groups/{schedule_id}")


# -------------------------------
# SCHEDULE EMPLOYEES
# -------------------------------

def add_employee_to_schedule(schedule_id, employee_id):
    return post(
        f"/api/schedule-groups/{schedule_id}/scheduleGroupEmployees/{employee_id}"
    )


def remove_employee_from_schedule(schedule_id, employee_id):
    return _request("DELETE", SCHEDULER_BASE_URL, f"/api/schedule-groups/{schedule_id}/scheduleGroupEmployees/{employee_id}")


# -------------------------------
# EMPLOYEE CRUD
# -------------------------------

def get_all_employees(params=None):
    return _get_employee_api("/api/employees", params=params)


def get_employee(employee_id):
    return _get_employee_api(f"/api/employees/{employee_id}")


def create_employee(first_name, last_name, email, role_id=1):
    return _post_employee_api(
        "/api/employees",
        {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "roleId": role_id
        }
    )


def update_employee(employee_id, first_name, last_name, email, role_id=None):
    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email
    }

    if role_id is not None:
        payload["roleId"] = role_id

    return _put_employee_api(f"/api/employees/{employee_id}", payload)


def delete_employee(employee_id):
    return _delete_employee_api(f"/api/employees/{employee_id}")
