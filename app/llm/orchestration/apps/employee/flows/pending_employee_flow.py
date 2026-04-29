import re


def handle_pending_employee_flow(
    *,
    message: str,
    token: str,
    session: dict,
    pending_employee_operation: dict | None,
    operations: dict,
    call_api,
    extract_employee_name_parts,
    extract_role_id,
    extract_explicit_employee_id,
    resolve_employee_id,
    set_pending_employee_operation_state,
    clear_pending_employee_operation_state,
    **_unused,
):
    if not pending_employee_operation:
        return None

    employees = call_api(token, operations["searchEmployees"], {"query": ""}) or []
    action = pending_employee_operation.get("action")
    first_name, last_name = extract_employee_name_parts(message)
    role_id = extract_role_id(message)
    if first_name and not pending_employee_operation.get("firstName"):
        pending_employee_operation["firstName"] = first_name
    if last_name and not pending_employee_operation.get("lastName"):
        pending_employee_operation["lastName"] = last_name
    if role_id and pending_employee_operation.get("roleId") is None:
        pending_employee_operation["roleId"] = role_id

    if action in {"update", "delete"} and pending_employee_operation.get("employeeId") is None:
        resolved_id = extract_explicit_employee_id(message)
        if resolved_id is None:
            lookup_name = " ".join(filter(None, [pending_employee_operation.get("firstName"), pending_employee_operation.get("lastName")])).strip()
            if not lookup_name and first_name and last_name:
                lookup_name = f"{first_name} {last_name}"
            if lookup_name:
                resolution = resolve_employee_id(token, lookup_name, operations, call_api)
                if resolution and resolution.get("type") == "resolved":
                    pending_employee_operation["employeeId"] = resolution["employeeId"]
                elif resolution and resolution.get("type") == "disambiguation":
                    pending_employee_operation["employeeOptions"] = resolution["raw"]
                    set_pending_employee_operation_state(session, pending_employee_operation)
                    lines = [f"{idx + 1}. {value}" for idx, value in enumerate(resolution["options"])]
                    return "I found multiple employees. Please choose one:\n" + "\n".join(lines)
        else:
            pending_employee_operation["employeeId"] = resolved_id

        choice = re.search(r"\b(\d+)\b", message or "")
        options = pending_employee_operation.get("employeeOptions") or []
        if pending_employee_operation.get("employeeId") is None and choice and options:
            idx = int(choice.group(1))
            if 1 <= idx <= len(options):
                pending_employee_operation["employeeId"] = options[idx - 1]["id"]
                pending_employee_operation["employeeOptions"] = []
            else:
                lines = [f"{i + 1}. {(item.get('firstName') or '').strip()} {(item.get('lastName') or '').strip()}".strip() for i, item in enumerate(options)]
                return "That number is out of range. Please choose one:\n" + "\n".join(lines)

    if action == "create":
        missing = []
        if not pending_employee_operation.get("firstName"):
            missing.append("first name")
        if not pending_employee_operation.get("lastName"):
            missing.append("last name")
        if pending_employee_operation.get("roleId") is None:
            missing.append("role (employee or supervisor)")
        if missing:
            set_pending_employee_operation_state(session, pending_employee_operation)
            return "I can add that employee. Please provide: " + ", ".join(missing) + "."
        payload = {
            "firstName": pending_employee_operation["firstName"],
            "lastName": pending_employee_operation["lastName"],
            "roleId": pending_employee_operation["roleId"],
        }
        created = call_api(token, operations["createEmployee"], payload)
        clear_pending_employee_operation_state(session)
        created_id = created.get("id")
        return f"Done — created employee {payload['firstName']} {payload['lastName']}" + (f" (ID: {created_id})." if created_id is not None else ".")

    if action == "update":
        if pending_employee_operation.get("employeeId") is None:
            set_pending_employee_operation_state(session, pending_employee_operation)
            return "Which employee should I update? Please provide name or employeeId."
        update_payload = {"employeeId": pending_employee_operation["employeeId"]}
        if pending_employee_operation.get("firstName"):
            update_payload["firstName"] = pending_employee_operation["firstName"]
        if pending_employee_operation.get("lastName"):
            update_payload["lastName"] = pending_employee_operation["lastName"]
        if pending_employee_operation.get("roleId") is not None:
            update_payload["roleId"] = pending_employee_operation["roleId"]
        if len(update_payload) == 1:
            set_pending_employee_operation_state(session, pending_employee_operation)
            return "What should I change? You can provide first name, last name, and/or role."
        call_api(token, operations["updateEmployee"], update_payload)
        employee = next((emp for emp in employees if emp.get("id") == pending_employee_operation["employeeId"]), None)
        clear_pending_employee_operation_state(session)
        employee_display = (
            f"{(employee.get('firstName') or '').strip()} {(employee.get('lastName') or '').strip()}".strip()
            if employee else f"employee {update_payload['employeeId']}"
        )
        return f"Done — updated {employee_display}."

    if action == "delete":
        if pending_employee_operation.get("employeeId") is None:
            set_pending_employee_operation_state(session, pending_employee_operation)
            return "Which employee should I delete? Please provide name or employeeId."
        call_api(token, operations["deleteEmployee"], {"employeeId": pending_employee_operation["employeeId"]})
        employee = next((emp for emp in employees if emp.get("id") == pending_employee_operation["employeeId"]), None)
        clear_pending_employee_operation_state(session)
        employee_display = (
            f"{(employee.get('firstName') or '').strip()} {(employee.get('lastName') or '').strip()}".strip()
            if employee else f"employee {pending_employee_operation['employeeId']}"
        )
        return f"Done — deleted {employee_display}."

    return None
