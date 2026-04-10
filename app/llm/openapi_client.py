import requests

BASE_URL = "https://localhost:7259"

def call_api(token, operation, args):
    url = BASE_URL + operation["path"]

    # 🔥 Handle path params
    for param in operation["parameters"]:
        if param["in"] == "path":
            name = param["name"]
            if name in args:
                url = url.replace(f"{{{name}}}", str(args.pop(name)))

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    method = operation["method"]
    print("----- EXECUTING API -----")
    print("Operation:", operation)
    print("Args:", args)
    if method == "GET":
        res = requests.get(url, params=args, headers=headers, verify=False)
    elif method == "POST":
        res = requests.post(url, json=args, headers=headers, verify=False)
    elif method == "PUT":
        res = requests.put(url, json=args, headers=headers, verify=False)
    elif method == "DELETE":
        res = requests.delete(url, headers=headers, verify=False)
    else:
        raise Exception(f"Unsupported method {method}")

    result = res.json() if res.text else {}

    print("----- API RESULT -----")
    print("URL:", url)
    print(result)
    print("STATUS:", res.status_code)
    print("RAW RESPONSE:", res.text)
    return result