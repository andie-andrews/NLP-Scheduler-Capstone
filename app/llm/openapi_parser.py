def parse_operations(spec):
    operations = {}

    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            op_id = details.get("operationId")
            if not op_id:
                continue

            operations[op_id] = {
                "method": method.upper(),
                "path": path,
                "parameters": details.get("parameters", []),
                "requestBody": details.get("requestBody"),
                "summary": details.get("summary", "")
            }

    return operations