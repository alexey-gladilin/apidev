from pathlib import Path

import pytest

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project(
    project_dir: Path,
    scaffold: bool = True,
    scaffold_dir: str = "integration",
    generated_dir: str = ".apidev/output/api",
    scaffold_write_policy: str = "create-missing",
) -> None:
    (project_dir / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        f"""
[paths]
templates_dir = ".apidev/templates"

[inputs]
contracts_dir = ".apidev/contracts"
shared_models_dir = ".apidev/models"

[generator]
generated_dir = "{generated_dir}"
scaffold = {str(scaffold).lower()}
scaffold_dir = "{scaffold_dir}"
scaffold_write_policy = "{scaffold_write_policy}"
""".strip() + "\n",
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
""".strip() + "\n",
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

    planned_paths = {change.path.resolve() for change in plan.changes}
    scaffold_root = (tmp_path / "integration").resolve()
    expected_paths = {
        scaffold_root / "handler_registry.py",
        scaffold_root / "router_factory.py",
        scaffold_root / "auth_registry.py",
        scaffold_root / "error_mapper.py",
    }
    assert expected_paths.issubset(planned_paths)


def test_diff_service_scaffold_router_factory_uses_apirouter_adapter(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_dir="integration")

    plan = _create_service().run(tmp_path)

    router_factory_change = next(
        change for change in plan.changes if change.path.name == "router_factory.py"
    )
    assert "def build_router() -> APIRouter:" in router_factory_change.content
    assert "router.add_api_route(" in router_factory_change.content
    assert "runtime_router_adapter" not in router_factory_change.content
    assert "Invalid operation metadata" in router_factory_change.content


def test_diff_service_does_not_plan_scaffold_when_disabled(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")

    plan = _create_service().run(tmp_path)

    planned_paths = {change.path.resolve() for change in plan.changes}
    assert (tmp_path / "integration" / "handler_registry.py").resolve() not in planned_paths


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
    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    scaffold_file = tmp_path / "integration" / "custom_handler.py"
    stale_file = generated_dir_path / "billing" / "models" / "obsolete_model.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    stale_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# user-owned scaffold\n", encoding="utf-8")
    stale_file.write_text("# stale\n", encoding="utf-8")

    plan = _create_service().run(tmp_path)

    remove_paths = {
        change.path.resolve() for change in plan.changes if change.change_type == "REMOVE"
    }
    assert scaffold_file.resolve() not in remove_paths
    assert stale_file.resolve() in remove_paths


def test_diff_service_scaffold_override_protects_existing_scaffold_files_from_remove(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")
    scaffold_file = tmp_path / "integration" / "custom_handler.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# user-owned scaffold\n", encoding="utf-8")

    plan = _create_service().run(tmp_path, scaffold=True)

    remove_paths = {
        change.path.resolve() for change in plan.changes if change.change_type == "REMOVE"
    }
    assert scaffold_file.resolve() not in remove_paths


def test_diff_service_does_not_plan_remove_for_external_scaffold_files_when_config_disables_scaffold(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")
    scaffold_file = tmp_path / "integration" / "custom_handler.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# stale scaffold\n", encoding="utf-8")

    plan = _create_service().run(tmp_path)

    remove_paths = {
        change.path.resolve() for change in plan.changes if change.change_type == "REMOVE"
    }
    assert scaffold_file.resolve() not in remove_paths


def test_diff_service_does_not_plan_remove_for_external_scaffold_files_when_glob_skips_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_project(tmp_path, scaffold=False, scaffold_dir="integration")
    scaffold_file = tmp_path / "integration" / "handler_registry.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# stale scaffold\n", encoding="utf-8")

    service = _create_service()
    original_glob = service.fs.glob

    def _glob_without_scaffold(path: Path, pattern: str):  # type: ignore[no-untyped-def]
        paths = list(original_glob(path, pattern))
        return [item for item in paths if "/integration/" not in item.as_posix()]

    monkeypatch.setattr(service.fs, "glob", _glob_without_scaffold)

    plan = service.run(tmp_path)

    remove_paths = {
        change.path.resolve() for change in plan.changes if change.change_type == "REMOVE"
    }
    assert scaffold_file.resolve() not in remove_paths


def test_diff_service_rejects_scaffold_dir_equal_to_generated_dir(tmp_path: Path) -> None:
    _write_project(
        tmp_path,
        scaffold=True,
        generated_dir="build/generated",
        scaffold_dir="build/generated",
    )

    with pytest.raises(ValueError, match="output contours"):
        _create_service().run(tmp_path)


def test_diff_service_rejects_scaffold_dir_nested_in_generated_dir(tmp_path: Path) -> None:
    _write_project(
        tmp_path,
        scaffold=True,
        generated_dir="build/generated",
        scaffold_dir="build/generated/scaffold",
    )

    with pytest.raises(ValueError, match="output contours"):
        _create_service().run(tmp_path)


def test_diff_service_rejects_generated_dir_nested_in_scaffold_dir(tmp_path: Path) -> None:
    _write_project(
        tmp_path,
        scaffold=True,
        generated_dir="build/generated",
        scaffold_dir="build",
    )

    with pytest.raises(ValueError, match="output contours"):
        _create_service().run(tmp_path)


def test_diff_service_rejects_generated_dir_escape_outside_project(tmp_path: Path) -> None:
    _write_project(
        tmp_path,
        scaffold=True,
        generated_dir="../outside-generated",
        scaffold_dir="integration",
    )

    with pytest.raises(ValueError, match="generated_dir"):
        _create_service().run(tmp_path)


def test_diff_service_rejects_scaffold_dir_symlink_escape_outside_project(tmp_path: Path) -> None:
    escaped_root = tmp_path.parent / "escaped-scaffold-target"
    escaped_root.mkdir(parents=True, exist_ok=True)
    link = tmp_path / "scaffold-link"
    link.symlink_to(escaped_root)

    _write_project(tmp_path, scaffold=True, scaffold_dir="scaffold-link/runtime")

    with pytest.raises(ValueError, match="project directory"):
        _create_service().run(tmp_path)


def test_diff_service_scaffold_policy_create_missing_keeps_existing_targets(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_write_policy="create-missing")
    scaffold_file = tmp_path / "integration" / "handler_registry.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# user-owned scaffold\n", encoding="utf-8")

    plan = _create_service().run(tmp_path)

    scaffold_change = next(
        change for change in plan.changes if change.path.resolve() == scaffold_file.resolve()
    )
    assert scaffold_change.change_type == "SAME"


def test_diff_service_scaffold_policy_skip_existing_keeps_existing_targets(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_write_policy="skip-existing")
    scaffold_file = tmp_path / "integration" / "handler_registry.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# user-owned scaffold\n", encoding="utf-8")

    plan = _create_service().run(tmp_path)

    scaffold_change = next(
        change for change in plan.changes if change.path.resolve() == scaffold_file.resolve()
    )
    assert scaffold_change.change_type == "SAME"


def test_diff_service_scaffold_policy_fail_on_conflict_raises_error(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_write_policy="fail-on-conflict")
    scaffold_file = tmp_path / "integration" / "handler_registry.py"
    scaffold_file.parent.mkdir(parents=True, exist_ok=True)
    scaffold_file.write_text("# user-owned scaffold\n", encoding="utf-8")

    with pytest.raises(ValueError, match="fail-on-conflict"):
        _create_service().run(tmp_path)


def test_diff_service_scaffold_policy_fail_on_conflict_adds_when_missing(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, scaffold=True, scaffold_write_policy="fail-on-conflict")

    plan = _create_service().run(tmp_path)

    target = (tmp_path / "integration" / "handler_registry.py").resolve()
    scaffold_change = next(change for change in plan.changes if change.path.resolve() == target)
    assert scaffold_change.change_type == "ADD"
