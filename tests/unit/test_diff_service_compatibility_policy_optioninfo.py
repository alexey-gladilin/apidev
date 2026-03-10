from pathlib import Path

import typer

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
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[paths]
templates_dir = ".apidev/templates"
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
intent: read
access_pattern: cached
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


def test_diff_service_accepts_typer_optioninfo_compatibility_policy(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "health/ping.yaml")
    option_policy = typer.Option(
        None,
        "--compatibility-policy",
        help="Compatibility policy gate for diagnostics: warn or strict.",
    )

    plan = _create_diff_service().run(tmp_path, compatibility_policy=option_policy)

    assert plan.compatibility_policy == "warn"
