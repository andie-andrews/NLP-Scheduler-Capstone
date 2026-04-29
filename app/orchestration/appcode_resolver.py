from __future__ import annotations

import json
from pathlib import Path


class AppcodeResolutionError(ValueError):
    """Raised when appcode is missing or not present in registry."""


_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "app_registry.json"


def load_registry_payload() -> dict:
    """Load the complete app registry payload from disk."""
    with _REGISTRY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_app_registry() -> dict:
    """Load only appcode definitions from the app registry payload."""
    return load_registry_payload().get("apps", {})


def resolve_appcode(appcode: str | None, registry: dict | None = None) -> tuple[str, dict]:
    if not appcode or not str(appcode).strip():
        raise AppcodeResolutionError("appcode is required")

    appcode_key = str(appcode).strip().lower()
    apps = registry or load_app_registry()
    if appcode_key not in apps:
        raise AppcodeResolutionError(f"unknown appcode '{appcode_key}'")

    return appcode_key, apps[appcode_key]
