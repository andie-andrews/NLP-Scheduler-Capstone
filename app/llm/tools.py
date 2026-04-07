import requests
from datetime import datetime, timedelta

BASE_URL = "https://localhost:7259/api"


# -------------------------------
# 📅 Helpers
# -------------------------------
def get_week_start(offset=0):
    today = datetime.today()
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    return start.strftime("%m/%d/%Y")  # REQUIRED FORMAT


# -------------------------------
# 👤 EMPLOYEES
# -------------------------------
def get_employee_by_name(name: str):
    res = requests.get(
        f"{BASE_URL}/employees",
        params={"query": name},
        verify=False
    )
    return res.json()


# -------------------------------
# 📊 SHIFTS (EMPLOYEE)
# -------------------------------
def get_employee_shifts(token, employee_id, week_offset=0):
    week_start = get_week_start(week_offset)

    res = requests.get(
        f"{BASE_URL}/employees/{employee_id}/shifts",
        params={"weekStart": week_start},
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    return res.json()


# -------------------------------
# ➕ CREATE SHIFT
# -------------------------------
def create_shift(token, schedule_id, employee_id, date, time, duration):
    payload = {
        "employeeId": employee_id,
        "start": f"{date}T{time}",
        "durationHours": duration
    }

    res = requests.post(
        f"{BASE_URL}/schedules/{schedule_id}/shifts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    return res.json()


# -------------------------------
# ✏️ UPDATE SHIFT (⚠️ NOT IN SPEC)
# -------------------------------
def update_shift(shift_id, date=None, time=None, duration=None):
    # NOTE: Your OpenAPI does NOT define update shift
    # Keeping this for now if your backend supports it

    payload = {}

    if date and time:
        payload["start"] = f"{date}T{time}"

    if duration:
        payload["durationHours"] = duration

    res = requests.put(
        f"{BASE_URL}/shifts/{shift_id}",
        json=payload,
        verify=False
    )

    return res.json()


# -------------------------------
# ❌ DELETE SHIFT
# -------------------------------
def delete_shift(token, shift_id):
    res = requests.delete(
        f"{BASE_URL}/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    return res.status_code == 200