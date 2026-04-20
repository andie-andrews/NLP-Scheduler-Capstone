import requests
import os
import urllib3

DEFAULT_BASE_URL = "https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net"


def _base_url() -> str:
    return os.getenv("SCHEDULER_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _verify_ssl() -> bool:
    verify_ssl = os.getenv("SCHEDULER_API_VERIFY_SSL", "true").lower() == "true"
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return verify_ssl


def _request_timeout_seconds() -> float:
    return float(os.getenv("SCHEDULER_API_TIMEOUT_SECONDS", "20"))


def _normalize_employee_search_result(operation, result):
    if operation.get("method") != "GET" or operation.get("path") != "/api/employees":
        return result

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        for key in ("items", "employees", "results", "data", "value", "content"):
            candidate = result.get(key)
            if isinstance(candidate, list):
                return candidate

    return result

def call_api(token, operation, args):
    # Avoid mutating caller-owned args (some flows reuse args after API calls).
    request_args = dict(args or {})
    verify_ssl = _verify_ssl()
    request_timeout_seconds = _request_timeout_seconds()
    url = _base_url() + operation["path"]
    request_body_schema = (
        (operation.get("requestBody") or {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    request_body_props = set((request_body_schema.get("properties") or {}).keys())

    # 🔥 Handle path params
    for param in operation["parameters"]:
        if param["in"] == "path":
            name = param["name"]
            if name in request_args:
                path_value = request_args[name]
                url = url.replace(f"{{{name}}}", str(path_value))
                if name not in request_body_props:
                    request_args.pop(name)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    method = operation["method"]
    local_employee_query = None
    if (
        method == "GET"
        and operation.get("path") == "/api/employees"
        and isinstance(request_args.get("query"), str)
        and request_args.get("query", "").strip()
    ):
        # Workaround: some API environments hang for non-empty employee query values.
        # Fetch full directory and filter locally.
        local_employee_query = request_args["query"].strip().lower()
        request_args["query"] = ""

    print("----- EXECUTING API -----")
    print("Operation:", operation)
    print("Args:", request_args)
    try:
        if method == "GET":
            res = requests.get(
                url,
                params=request_args,
                headers=headers,
                verify=verify_ssl,
                timeout=request_timeout_seconds,
            )
        elif method == "POST":
            res = requests.post(
                url,
                json=request_args,
                headers=headers,
                verify=verify_ssl,
                timeout=request_timeout_seconds,
            )
        elif method == "PUT":
            res = requests.put(
                url,
                json=request_args,
                headers=headers,
                verify=verify_ssl,
                timeout=request_timeout_seconds,
            )
        elif method == "PATCH":
            res = requests.patch(
                url,
                json=request_args,
                headers=headers,
                verify=verify_ssl,
                timeout=request_timeout_seconds,
            )
        elif method == "DELETE":
            res = requests.delete(
                url,
                headers=headers,
                verify=verify_ssl,
                timeout=request_timeout_seconds,
            )
        else:
            raise Exception(f"Unsupported method {method}")
    except requests.RequestException as exc:
        print("----- API ERROR -----")
        print("URL:", url)
        print("ERROR:", str(exc))
        return {
            "__httpStatus": 0,
            "error": f"API request failed: {exc}",
            "url": url,
            "args": request_args,
        }

    if not res.text:
        result = {}
    else:
        try:
            result = res.json()
        except ValueError:
            result = {
                "statusCode": res.status_code,
                "rawText": res.text,
            }

    result = _normalize_employee_search_result(operation, result)

    if isinstance(result, dict) and "__httpStatus" not in result:
        result["__httpStatus"] = res.status_code

    if local_employee_query and isinstance(result, list):
        result = [
            employee
            for employee in result
            if isinstance(employee, dict)
            and local_employee_query in (
                f"{(employee.get('firstName') or '').strip()} {(employee.get('lastName') or '').strip()}".strip().lower()
            )
        ]

    print("----- API RESULT -----")
    print("URL:", url)
    print(result)
    print("STATUS:", res.status_code)
    print("RAW RESPONSE:", res.text)
    return result
