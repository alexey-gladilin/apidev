from pathlib import Path

import pytest

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project(project_dir: Path, scaffold: bool = True, scaffold_dir: str = "integration") -> None:
    (project_dir / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        f"""
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"
scaffold = {str(scaffold).lower()}
scaffold_dir = "{scaffold_dir}"

[templates]
dir = ".apidev/templates"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (project_dir / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body: {type: object}
errors: []
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _create_service() -> DiffService:
    fs = LocalFileSystem()
    return DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )


def test_diff_service_plans_scaffold_files_when_enabled(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_dir="integration")

    plan = _create_service().run(tmp_path)

    planned_relpaths = {change.path.relative_to(plan.generated_root).as_posix() for change in plan.changes}
    assert "integration/handler_registry.py" in planned_relpaths
    assert "integration/router_factory.py" in planned_relpaths
    assert "integration/auth_registry.py" in planned_relpaths
    assert "integration/error_mapper.py" in planned_relpaths


def test_diff_service_does_not_plan_scaffold_when_disabled(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")

    plan = _create_service().run(tmp_path)

    planned_relpaths = {change.path.relative_to(plan.generated_root).as_posix() for change in plan.changes}
    assert "integration/handler_registry.py" not in planned_relpaths


def test_diff_service_rejects_absolute_scaffold_dir(tmp_path: Path) -> None:
    absolute_dir = str((tmp_path / "outside").resolve())
    _write_project(tmp_path, scaffold=True, scaffold_dir=absolute_dir)

    with pytest.raises(ValueError, match="scaffold_dir"):
        _create_service().run(tmp_path)


def test_diff_service_rejects_scaffold_dir_escape(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_dir="../outside")

    with pytest.raises(ValueError, match="scaffold_dir"):
        _create_service().run(tmp_path)


def test_diff_service_does_not_remove_existing_scaffold_python_files_when_enabled(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_dir="integration")
    generated_root = tmp_path / ".apidev" / "output" / "api"
    scaffold_file = generated_root / "integration" / "custom_handler.py"
    stale_file = generated_root / "billing" / "models" / "obsolete_model.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    stale_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# user-owned scaffold\n", encoding="utf-8")
    stale_file.write_text("# stale\n", encoding="utf-8")

    plan = _create_service().run(tmp_path)

    remove_relpaths = sorted(
        change.path.relative_to(generated_root).as_posix()
        for change in plan.changes
        if change.change_type == "REMOVE"
    )
    assert "integration/custom_handler.py" not in remove_relpaths
    assert "billing/models/obsolete_model.py" in remove_relpaths


def test_diff_service_scaffold_override_protects_existing_scaffold_files_from_remove(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")
    generated_root = tmp_path / ".apidev" / "output" / "api"
    scaffold_file = generated_root / "integration" / "custom_handler.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# user-owned scaffold\n", encoding="utf-8")

    plan = _create_service().run(tmp_path, scaffold=True)

    remove_relpaths = {
        change.path.relative_to(generated_root).as_posix()
        for change in plan.changes
        if change.change_type == "REMOVE"
    }
    assert "integration/custom_handler.py" not in remove_relpaths


def test_diff_service_plans_remove_for_scaffold_files_when_config_disables_scaffold(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")
    generated_root = tmp_path / ".apidev" / "output" / "api"
    scaffold_file = generated_root / "integration" / "custom_handler.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# stale scaffold\n", encoding="utf-8")

    plan = _create_service().run(tmp_path)

    remove_relpaths = {
        change.path.relative_to(generated_root).as_posix()
        for change in plan.changes
        if change.change_type == "REMOVE"
    }
    assert "integration/custom_handler.py" in remove_relpaths


def test_diff_service_plans_remove_for_configured_scaffold_dir_when_disabled_even_if_glob_skips_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")
    generated_root = tmp_path / ".apidev" / "output" / "api"
    scaffold_file = generated_root / "integration" / "handler_registry.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# stale scaffold\n", encoding="utf-8")

    service = _create_service()
    original_glob = service.fs.glob

    def _glob_without_scaffold(path: Path, pattern: str):  # type: ignore[no-untyped-def]
        paths = list(original_glob(path, pattern))
        return [item for item in paths if "integration/" not in item.as_posix()]

    monkeypatch.setattr(service.fs, "glob", _glob_without_scaffold)

    plan = service.run(tmp_path)

    remove_relpaths = {
        change.path.relative_to(generated_root).as_posix()
        for change in plan.changes
        if change.change_type == "REMOVE"
    }
    assert "integration/handler_registry.py" in remove_relpaths
