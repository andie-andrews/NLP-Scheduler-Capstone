import re


def parse_operations_by_api(specs_by_api):
    operations = {}

    for api_name, spec in specs_by_api.items():
        for path, methods in spec["paths"].items():
            path_parameters = methods.get("parameters", [])
            sibling_path_params = {}
            for sibling_method, sibling_details in methods.items():
                if sibling_method == "parameters":
                    continue
                for sibling_param in sibling_details.get("parameters", []):
                    if sibling_param.get("in") == "path" and sibling_param.get("name"):
                        sibling_path_params.setdefault(sibling_param["name"], sibling_param)

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
                    inferred_param = sibling_path_params.get(template_name, {})
                    merged_parameters.append({
                        "name": template_name,
                        "in": "path",
                        "required": True,
                        "schema": inferred_param.get("schema", {"type": "string"}),
                        "description": "Inferred from URL template.",
                    })

                callable_id = f"{api_name}__{op_id}"
                operations[callable_id] = {
                    "api_name": api_name,
                    "operationId": op_id,
                    "callable_id": callable_id,
                    "method": method.upper(),
                    "path": path,
                    "servers": spec.get("servers", []),
                    "parameters": merged_parameters,
                    "requestBody": details.get("requestBody"),
                    "summary": details.get("summary", ""),
                    "intent_phrases": details.get("x-intent", []),
                    "dependencies": details.get("x-dependencies", {}),
                }

    return operations


def parse_operations(spec):
    parsed = parse_operations_by_api({"default": spec})
    return {op["operationId"]: op for op in parsed.values()}
