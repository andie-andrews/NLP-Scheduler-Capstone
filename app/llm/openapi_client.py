import requests

BASE_URL = "https://localhost:7259"

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
    print("----- EXECUTING API -----")
    print("Operation:", operation)
    print("Args:", request_args)
    if method == "GET":
        res = requests.get(url, params=request_args, headers=headers, verify=False)
    elif method == "POST":
        res = requests.post(url, json=request_args, headers=headers, verify=False)
    elif method == "PUT":
        res = requests.put(url, json=request_args, headers=headers, verify=False)
    elif method == "DELETE":
        res = requests.delete(url, headers=headers, verify=False)
    else:
        raise Exception(f"Unsupported method {method}")

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

    print("----- API RESULT -----")
    print("URL:", url)
    print(result)
    print("STATUS:", res.status_code)
    print("RAW RESPONSE:", res.text)
    return result
