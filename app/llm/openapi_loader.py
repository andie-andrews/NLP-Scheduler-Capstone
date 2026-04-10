import json
import jsonref
from pathlib import Path

SPEC_PATH = Path(__file__).parent.parent.parent / ".openapi" / "scheduler.api.json"

def load_openapi_spec():
    with open(SPEC_PATH, "r") as f:
        return jsonref.loads(f.read())