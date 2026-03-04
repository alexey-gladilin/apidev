from pathlib import Path

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


def test_diff_service_plans_remove_for_stale_generated_artifact(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "health/ping.yaml")

    stale_path = tmp_path / ".apidev" / "output" / "api" / "routers" / "stale_router.py"
    stale_path.parent.mkdir(parents=True, exist_ok=True)
    stale_path.write_text("# stale", encoding="utf-8")

    plan = _create_diff_service().run(tmp_path)

    removes = [change for change in plan.changes if change.change_type == "REMOVE"]
    assert len(removes) == 1
    assert removes[0].path == stale_path


def test_diff_service_plans_remove_in_deterministic_path_order(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "health/ping.yaml")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    stale_b = generated_dir_path / "transport" / "models" / "zzz_stale.py"
    stale_a = generated_dir_path / "transport" / "models" / "aaa_stale.py"
    stale_b.parent.mkdir(parents=True, exist_ok=True)
    stale_b.write_text("# stale-b", encoding="utf-8")
    stale_a.write_text("# stale-a", encoding="utf-8")

    plan = _create_diff_service().run(tmp_path)

    remove_paths = [
        change.path.relative_to(generated_dir_path).as_posix()
        for change in plan.changes
        if change.change_type == "REMOVE"
    ]
    assert remove_paths == [
        "transport/models/aaa_stale.py",
        "transport/models/zzz_stale.py",
    ]
