import os
from pathlib import Path

import jsonref

OPENAPI_MANIFEST_ENV_VAR = "SCHEDULER_OPENAPI_SPECS"
DEFAULT_API_NAME = "scheduler"
DEFAULT_SPEC_PATH = Path(__file__).parent.parent.parent / ".openapi" / "scheduler.api.json"


def parse_openapi_manifest(manifest: str) -> dict[str, Path]:
    specs: dict[str, Path] = {}

    for raw_entry in manifest.split(","):
        entry = raw_entry.strip()
        if not entry:
            continue

        api_name, separator, raw_path = entry.partition("=")
        if not separator:
            raise ValueError(
                f"Invalid manifest entry '{entry}'. Expected format 'api_name=spec_path'."
            )

        api_name = api_name.strip()
        spec_path = raw_path.strip()

        if not api_name or not spec_path:
            raise ValueError(
                f"Invalid manifest entry '{entry}'. Expected non-empty api_name and spec_path."
            )

        specs[api_name] = Path(spec_path)

    if not specs:
        raise ValueError(
            f"{OPENAPI_MANIFEST_ENV_VAR} was provided but no valid entries were found."
        )

    return specs


def _resolve_spec_manifest() -> dict[str, Path]:
    manifest = os.getenv(OPENAPI_MANIFEST_ENV_VAR)

    if not manifest:
        return {DEFAULT_API_NAME: DEFAULT_SPEC_PATH}

    return parse_openapi_manifest(manifest)


def load_openapi_spec() -> dict[str, dict]:
    specs = {}

    for api_name, spec_path in _resolve_spec_manifest().items():
        with open(spec_path, "r") as f:
            specs[api_name] = jsonref.loads(f.read())

    return specs
