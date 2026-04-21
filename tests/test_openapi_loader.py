import json

import pytest

from app.llm.openapi_loader import (
    DEFAULT_API_NAME,
    OPENAPI_MANIFEST_ENV_VAR,
    load_openapi_spec,
    parse_openapi_manifest,
)


def test_load_openapi_spec_falls_back_to_default_directory_when_manifest_missing(monkeypatch, tmp_path):
    spec_dir = tmp_path / ".openapi"
    spec_dir.mkdir()

    scheduler_spec = {"openapi": "3.0.0", "info": {"title": "scheduler", "version": "1.0"}, "paths": {}}
    employee_spec = {"openapi": "3.0.0", "info": {"title": "employee", "version": "1.0"}, "paths": {}}

    (spec_dir / "scheduler.api.json").write_text(json.dumps(scheduler_spec))
    (spec_dir / "employee.api.json").write_text(json.dumps(employee_spec))

    monkeypatch.delenv(OPENAPI_MANIFEST_ENV_VAR, raising=False)
    monkeypatch.setattr("app.llm.openapi_loader.DEFAULT_SPEC_DIRECTORY", spec_dir)
    monkeypatch.setattr("app.llm.openapi_loader.DEFAULT_SPEC_PATH", spec_dir / "scheduler.api.json")

    loaded_specs = load_openapi_spec()

    assert set(loaded_specs.keys()) == {"scheduler", "employee"}
    assert loaded_specs["scheduler"]["info"]["title"] == "scheduler"
    assert loaded_specs["employee"]["info"]["title"] == "employee"


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


def test_load_openapi_spec_supports_directory_entries(monkeypatch, tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()

    (spec_dir / "auth.api.json").write_text(
        json.dumps({"openapi": "3.0.0", "info": {"title": "auth"}, "paths": {}})
    )
    (spec_dir / "employee.json").write_text(
        json.dumps({"openapi": "3.0.0", "info": {"title": "employee"}, "paths": {}})
    )

    monkeypatch.setenv(OPENAPI_MANIFEST_ENV_VAR, f"all={spec_dir}")

    loaded_specs = load_openapi_spec()

    assert set(loaded_specs.keys()) == {"auth", "employee"}
    assert loaded_specs["auth"]["info"]["title"] == "auth"
    assert loaded_specs["employee"]["info"]["title"] == "employee"


def test_parse_openapi_manifest_resolves_relative_paths_from_repo_root(monkeypatch, tmp_path):
    project_root = tmp_path / "repo-root"
    app_dir = project_root / "app"
    app_dir.mkdir(parents=True)

    monkeypatch.setattr("app.llm.openapi_loader.ROOT_DIR", project_root)
    manifest = "scheduler=.openapi/scheduler.api.json,auth=specs/auth.json"

    parsed_manifest = parse_openapi_manifest(manifest)

    assert parsed_manifest == {
        "scheduler": project_root / ".openapi" / "scheduler.api.json",
        "auth": project_root / "specs" / "auth.json",
    }
