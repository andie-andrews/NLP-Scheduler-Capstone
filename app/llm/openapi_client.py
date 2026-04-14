import requests
import os
import urllib3

BASE_URL = os.getenv("SCHEDULER_API_BASE_URL", "https://nlp-scheduler-api-ehc5bhhdeparezd7.canadacentral-01.azurewebsites.net").rstrip("/")
VERIFY_SSL = os.getenv("SCHEDULER_API_VERIFY_SSL", "true").lower() == "true"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("SCHEDULER_API_TIMEOUT_SECONDS", "20"))

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def call_api(token, operation, args):
    # Avoid mutating caller-owned args (some flows reuse args after API calls).
    request_args = dict(args or {})
    url = BASE_URL + operation["path"]
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
                verify=VERIFY_SSL,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        elif method == "POST":
            res = requests.post(
                url,
                json=request_args,
                headers=headers,
                verify=VERIFY_SSL,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        elif method == "PUT":
            res = requests.put(
                url,
                json=request_args,
                headers=headers,
                verify=VERIFY_SSL,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        elif method == "DELETE":
            res = requests.delete(
                url,
                headers=headers,
                verify=VERIFY_SSL,
                timeout=REQUEST_TIMEOUT_SECONDS,
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

    if isinstance(result, dict) and "__httpStatus" not in result:
        result["__httpStatus"] = res.status_code

    if local_employee_query and isinstance(result, list):
        result = [
            employee
            for employee in result
            if local_employee_query in (
                f"{(employee.get('firstName') or '').strip()} {(employee.get('lastName') or '').strip()}".strip().lower()
            )
        ]

    print("----- API RESULT -----")
    print("URL:", url)
    print(result)
    print("STATUS:", res.status_code)
    print("RAW RESPONSE:", res.text)
    return result
