from pathlib import Path
from typing import Any, cast

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project_config(project_dir: Path) -> None:
    (project_dir / ".apidev" / "contracts").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"
""".strip(),
        encoding="utf-8",
    )


def _write_contract(project_dir: Path, relpath: str) -> None:
    target = project_dir / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """
method: GET
path: /v1/ping
auth: public
summary: Ping
description: Ping endpoint
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )


def _create_diff_service() -> DiffService:
    fs = LocalFileSystem()
    return DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )


def test_diff_service_remove_challenge_ignores_non_python_stale_files(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "health/ping.yaml")

    generated_root = tmp_path / ".apidev" / "output" / "api"
    stale_txt = generated_root / "routers" / "stale_router.txt"
    stale_txt.parent.mkdir(parents=True, exist_ok=True)
    stale_txt.write_text("stale text artifact", encoding="utf-8")

    plan = _create_diff_service().run(tmp_path)

    assert all(change.path != stale_txt for change in plan.changes)
    assert all(
        not (change.change_type == "REMOVE" and change.path.suffix != ".py")
        for change in plan.changes
    )


def test_diff_service_remove_challenge_never_targets_outside_generated_root(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "health/ping.yaml")

    outside_stale = tmp_path / "manual" / "stale_router.py"
    outside_stale.parent.mkdir(parents=True, exist_ok=True)
    outside_stale.write_text("# manual stale", encoding="utf-8")

    plan = _create_diff_service().run(tmp_path)

    assert all(change.path != outside_stale for change in plan.changes)
    assert all(
        change.path.is_relative_to(plan.generated_root)
        for change in plan.changes
        if change.change_type == "REMOVE"
    )


def test_diff_service_remove_challenge_accepts_none_policy(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "health/ping.yaml")

    plan = _create_diff_service().run(tmp_path, compatibility_policy=cast(Any, None))

    assert plan.compatibility_policy == "warn"
