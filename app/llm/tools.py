import requests
from datetime import datetime, timedelta
import os

def _runtime_environment() -> str:
    for env_var in ("SCHEDULER_RUNTIME_ENV", "APP_ENV", "ASPNETCORE_ENVIRONMENT", "ENVIRONMENT"):
        env_value = os.getenv(env_var)
        if env_value and env_value.strip():
            return env_value.strip().lower()
    return "development"


def _default_base_url() -> str:
    if _runtime_environment() in {"production", "prod"}:
        return "https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net"
    return "http://localhost/schedulerapi"


BASE_URL = os.getenv("SCHEDULER_API_BASE_URL", _default_base_url()).rstrip("/") + "/api"
VERIFY_SSL = os.getenv("SCHEDULER_API_VERIFY_SSL", "true").lower() == "true"


# -------------------------------
# Helpers
# -------------------------------
def get_week_start(offset=0):
    today = datetime.today()
    days_since_sunday = (today.weekday() + 1) % 7
    start = today - timedelta(days=days_since_sunday) + timedelta(weeks=offset)
    return start.strftime("%m/%d/%Y")  # REQUIRED FORMAT

def parse_datetime(date_str, time_str):
    now = datetime.now()

    # -----------------------
    # 📅 DATE PARSING
    # -----------------------
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    date_str = date_str.lower()

    if date_str in days:
        target_day = days[date_str]
        days_ahead = target_day - now.weekday()

        if days_ahead <= 0:
            days_ahead += 7

        target_date = now + timedelta(days=days_ahead)
    else:
        target_date = now  # fallback

    # -----------------------
    # ⏰ TIME PARSING (FIXED)
    # -----------------------
    time_str = time_str.strip().lower()

    is_pm = "pm" in time_str
    is_am = "am" in time_str

    # Remove am/pm
    time_clean = time_str.replace("am", "").replace("pm", "").strip()

    # Handle "8:00" vs "8"
    if ":" in time_clean:
        hour_str, minute_str = time_clean.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
    else:
        hour = int(time_clean)
        minute = 0

    # Convert to 24-hour format
    if is_pm and hour != 12:
        hour += 12
    if is_am and hour == 12:
        hour = 0

    return datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        hour,
        minute,
        0
    )
# -------------------------------
# EMPLOYEES
# -------------------------------
def get_employee_by_name(token, query: str):
    url = f"{BASE_URL}/employees?query={query}"

    res = requests.get(url, 
                       headers={"Authorization": f"Bearer {token}"},
                       verify=VERIFY_SSL)
    print("INFO:", res.status_code, res.text)
    # 🔥 Add this
    if not res.ok:
        print("ERROR:", res.status_code, res.text)
        return []

    # 🔥 Guard JSON parsing
    if not res.text:
        return []

    try:
        return res.json()
    except Exception:
        print("INVALID JSON:", res.text)
        return []


# -------------------------------
# SHIFTS (EMPLOYEE)
# -------------------------------
def get_employee_shifts(token, employee_id, week_offset=0):
    week_start = datetime.strptime(get_week_start(week_offset), "%m/%d/%Y")
    week_end = week_start + timedelta(days=6)

    res = requests.get(
        f"{BASE_URL}/employees/{employee_id}/shifts",
        params={
            "startDate": week_start.date().isoformat(),
            "endDate": week_end.date().isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
        verify=VERIFY_SSL
    )

    return res.json()


# -------------------------------
# CREATE SHIFT
# -------------------------------
def create_shift(token, schedule_group_id, employee_id, date, time, duration_hours):
    url = f"{BASE_URL}/schedule-groups/{schedule_group_id}/shifts"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 🔥 Convert natural language → datetime
    dt = parse_datetime(date, time)

    payload = {
         # 🔥 REQUIRED WRAPPER
            "scheduleGroupId": schedule_group_id,
            "employeeId": employee_id,
            "start": dt.isoformat(),  
            "durationHours": duration_hours
    }

    print("CREATE SHIFT PAYLOAD:", payload)

    res = requests.post(url, json=payload, headers=headers, verify=VERIFY_SSL)

    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)



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
        verify=VERIFY_SSL
    )

    return res.json()


# -------------------------------
#  DELETE SHIFT
# -------------------------------
def delete_shift(token, shift_id):
    res = requests.delete(
        f"{BASE_URL}/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {token}"},
        verify=VERIFY_SSL
    )

    return res.status_code == 200
