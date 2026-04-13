def resolve_employee_id(token, name, operations, api_caller):
    search_op = operations.get("searchEmployees")

    if not search_op:
        return None

    results = api_caller(token, search_op, {"query": name})

    if not results:
        return {"type": "not_found", "name": name}

    if len(results) == 1:
        return {"type": "resolved", "employeeId": results[0]["id"]}

    options = [
        f"{r['firstName']} {r['lastName']} (ID: {r['id']})"
        for r in results
    ]

    return {
        "type": "disambiguation",
        "options": options,
        "raw": results
    }


def resolve_schedule_id(token, name, operations, api_caller):
    schedule_op = operations.get("getSchedules")

    if not schedule_op:
        return None

    target = (name or "").strip().lower()
    if not target:
        return {"type": "not_found", "name": name}

    schedules = api_caller(token, schedule_op, {"query": name}) or []
    if not schedules:
        schedules = api_caller(token, schedule_op, {}) or []
    if not schedules:
        return {"type": "not_found", "name": name}

    exact = [s for s in schedules if (s.get("name") or "").strip().lower() == target]
    if len(exact) == 1:
        return {"type": "resolved", "scheduleId": exact[0]["id"], "name": exact[0].get("name")}

    partial = [s for s in schedules if target in (s.get("name") or "").strip().lower()]
    if len(partial) == 1:
        return {"type": "resolved", "scheduleId": partial[0]["id"], "name": partial[0].get("name")}

    matches = exact or partial
    if matches:
        return {
            "type": "disambiguation",
            "options": [f"{s.get('name')} (ID: {s.get('id')})" for s in matches],
            "raw": matches
        }

    return {"type": "not_found", "name": name}


def normalize_schedule_id_arg(token, raw_value, operations, api_caller):
    if raw_value is None:
        return None
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, str):
        value = raw_value.strip()
        if value.isdigit():
            print("[create_shift][schedule] scheduleId provided as numeric string:", value)
            return int(value)
        resolution = resolve_schedule_id(token, value, operations, api_caller)
        if resolution and resolution.get("type") == "resolved":
            print("[create_shift][schedule] Resolved schedule name to ID:", resolution)
            return resolution["scheduleId"]
        print("[create_shift][schedule] Failed to resolve schedule:", value)
    return None
