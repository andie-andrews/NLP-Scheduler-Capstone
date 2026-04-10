from llm.orchestrator_old import handle_request  

def run_orchestrator(message: str, token: str, session: dict):
    return handle_request(
        message,
        role=session.get("role"),
        token=token,
        memory=session.get("memory"),
        employee_id=session.get("employee_id"),
    )