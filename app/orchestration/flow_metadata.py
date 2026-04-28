FLOW_METADATA: dict[str, dict[str, str]] = {
    "create_shift": {"domain": "schedule", "handler": "create_shift"},
    "update_shift": {"domain": "schedule", "handler": "update_shift"},
    "delete_shift": {"domain": "schedule", "handler": "delete_shift"},
    "create_schedule": {"domain": "schedule", "handler": "create_schedule"},
    "add_schedule_member": {"domain": "schedule", "handler": "add_schedule_member"},
    "remove_schedule_member": {"domain": "schedule", "handler": "remove_schedule_member"},
    "delete_schedule": {"domain": "schedule", "handler": "delete_schedule"},
    "get_manager_schedule_groups": {"domain": "schedule", "handler": "get_manager_schedule_groups"},
    "find_employee": {"domain": "employee", "handler": "find_employee"},
    "create_employee": {"domain": "employee", "handler": "create_employee"},
    "update_employee": {"domain": "employee", "handler": "update_employee"},
    "delete_employee": {"domain": "employee", "handler": "delete_employee"},
}
