import os

USE_ORCHESTRATOR_V2 = os.getenv("USE_ORCHESTRATOR_V2", "true").lower() == "true"

if USE_ORCHESTRATOR_V2:
    from llm.orchestrator_v2 import run_orchestrator as run_orchestrator
else:
    from llm.orchestrator_v1 import run_orchestrator as run_orchestrator
