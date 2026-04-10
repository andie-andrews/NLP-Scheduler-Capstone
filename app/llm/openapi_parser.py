import re


def parse_operations(spec):
    operations = {}

    for path, methods in spec["paths"].items():
        path_parameters = methods.get("parameters", [])
        for method, details in methods.items():
            if method == "parameters":
                continue
            op_id = details.get("operationId")
            if not op_id:
                continue

            operation_parameters = details.get("parameters", [])
            merged_parameters = path_parameters + operation_parameters

            existing_param_names = {p.get("name") for p in merged_parameters}
            template_params = re.findall(r"{([^{}]+)}", path)
            for template_name in template_params:
                if template_name in existing_param_names:
                    continue
                merged_parameters.append({
                    "name": template_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Inferred from URL template.",
                })

            operations[op_id] = {
                "method": method.upper(),
                "path": path,
                "parameters": merged_parameters,
                "requestBody": details.get("requestBody"),
                "summary": details.get("summary", ""),
                "intent_phrases": details.get("x-intent", []),
                "dependencies": details.get("x-dependencies", {}),
            }

    return operations
