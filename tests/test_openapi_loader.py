import json

import pytest

from app.llm.openapi_loader import (
    DEFAULT_API_NAME,
    OPENAPI_MANIFEST_ENV_VAR,
    load_openapi_spec,
    parse_openapi_manifest,
)


def test_load_openapi_spec_falls_back_to_default_when_manifest_missing(monkeypatch, tmp_path):
    spec = {"openapi": "3.0.0", "info": {"title": "scheduler", "version": "1.0"}, "paths": {}}
    spec_path = tmp_path / "scheduler.api.json"
    spec_path.write_text(json.dumps(spec))

    monkeypatch.delenv(OPENAPI_MANIFEST_ENV_VAR, raising=False)
    monkeypatch.setattr("app.llm.openapi_loader.DEFAULT_SPEC_PATH", spec_path)

    loaded_specs = load_openapi_spec()

    assert list(loaded_specs.keys()) == [DEFAULT_API_NAME]
    assert loaded_specs[DEFAULT_API_NAME]["info"]["title"] == "scheduler"


def test_parse_and_load_openapi_multi_spec_manifest(monkeypatch, tmp_path):
    auth_path = tmp_path / "auth.json"
    employee_path = tmp_path / "employee.json"
    scheduler_path = tmp_path / "scheduler.json"

    auth_path.write_text(json.dumps({"openapi": "3.0.0", "info": {"title": "auth"}, "paths": {}}))
    employee_path.write_text(json.dumps({"openapi": "3.0.0", "info": {"title": "employee"}, "paths": {}}))
    scheduler_path.write_text(json.dumps({"openapi": "3.0.0", "info": {"title": "scheduler"}, "paths": {}}))

    manifest = f"auth={auth_path},employee={employee_path},scheduler={scheduler_path}"
    monkeypatch.setenv(OPENAPI_MANIFEST_ENV_VAR, manifest)

    parsed_manifest = parse_openapi_manifest(manifest)
    loaded_specs = load_openapi_spec()

    assert parsed_manifest == {
        "auth": auth_path,
        "employee": employee_path,
        "scheduler": scheduler_path,
    }
    assert set(loaded_specs.keys()) == {"auth", "employee", "scheduler"}
    assert loaded_specs["auth"]["info"]["title"] == "auth"
    assert loaded_specs["employee"]["info"]["title"] == "employee"
    assert loaded_specs["scheduler"]["info"]["title"] == "scheduler"


def test_load_openapi_spec_raises_for_missing_manifest_file(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing.json"
    monkeypatch.setenv(OPENAPI_MANIFEST_ENV_VAR, f"auth={missing_path}")

    with pytest.raises(FileNotFoundError):
        load_openapi_spec()
