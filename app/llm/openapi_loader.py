import os
from pathlib import Path

import jsonref

OPENAPI_MANIFEST_ENV_VAR = "SCHEDULER_OPENAPI_SPECS"
DEFAULT_API_NAME = "scheduler"
ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SPEC_DIRECTORY = ROOT_DIR / ".openapi"
DEFAULT_SPEC_PATH = DEFAULT_SPEC_DIRECTORY / "scheduler.api.json"


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

        parsed_path = Path(spec_path)
        if not parsed_path.is_absolute():
            parsed_path = ROOT_DIR / parsed_path

        specs[api_name] = parsed_path.resolve(strict=False)

    if not specs:
        raise ValueError(
            f"{OPENAPI_MANIFEST_ENV_VAR} was provided but no valid entries were found."
        )

    return specs


def _resolve_spec_manifest() -> dict[str, Path]:
    manifest = os.getenv(OPENAPI_MANIFEST_ENV_VAR)

    if manifest:
        return parse_openapi_manifest(manifest)

    if DEFAULT_SPEC_DIRECTORY.is_dir():
        return {"all": DEFAULT_SPEC_DIRECTORY}

    return {DEFAULT_API_NAME: DEFAULT_SPEC_PATH}


def _derive_api_name_from_file(spec_file: Path) -> str:
    file_name = spec_file.name
    if file_name.endswith(".api.json"):
        return file_name[: -len(".api.json")]
    return spec_file.stem


def load_openapi_spec() -> dict[str, dict]:
    specs: dict[str, dict] = {}

    for configured_api_name, spec_path in _resolve_spec_manifest().items():
        if spec_path.is_dir():
            spec_files = sorted(spec_path.glob("*.json"))
            if not spec_files:
                raise FileNotFoundError(f"No .json spec files found in directory: {spec_path}")

            for spec_file in spec_files:
                api_name = _derive_api_name_from_file(spec_file)
                with open(spec_file, "r") as f:
                    specs[api_name] = jsonref.loads(f.read())
            continue

        with open(spec_path, "r") as f:
            specs[configured_api_name] = jsonref.loads(f.read())

    return specs
