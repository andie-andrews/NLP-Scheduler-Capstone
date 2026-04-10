def build_tools(operations):
    tools = []

    for op_id, op in operations.items():

        properties = {}
        required = []

        for param in op.get("parameters", []):
            name = param["name"]
            properties[name] = {
                "type": param.get("schema", {}).get("type", "string"),
                "description": param.get("description", "")
            }

            if param.get("required"):
                required.append(name)

        if op.get("requestBody"):
            content = op["requestBody"]["content"]["application/json"]["schema"]

            for prop, details in content.get("properties", {}).items():
                properties[prop] = {
                    "type": details.get("type", "string")
                }

            required += content.get("required", [])

        required = list(dict.fromkeys(required))

        tools.append({
            "type": "function",
            "function": {
                "name": op_id,
                "description": op["summary"] or op_id,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        })

    return tools


def sanitize_tools_for_openai(tools):
    sanitized = []
    for tool in tools:
        function = tool.get("function", {})
        parameters = function.get("parameters", {})
        properties = parameters.get("properties", {}) or {}
        required = parameters.get("required", []) or []

        unique_required = []
        seen = set()
        for name in required:
            if name in properties and name not in seen:
                unique_required.append(name)
                seen.add(name)

        parameters["required"] = unique_required
        function["parameters"] = parameters
        tool["function"] = function
        sanitized.append(tool)

    return sanitized
