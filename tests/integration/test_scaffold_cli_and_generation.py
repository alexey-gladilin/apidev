from pathlib import Path

from typer.testing import CliRunner

from apidev.application.services.generate_service import GenerateService
from apidev.cli import app
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.output.writer import SafeWriter
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

runner = CliRunner()


def _write_project(
    project_dir: Path, scaffold: bool = True, scaffold_dir: str = "integration"
) -> None:
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


def _run_generate(project_dir: Path) -> None:
    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=project_dir / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )
    _ = service.run(project_dir, baseline_ref="v1.0.0")


def test_gen_cli_scaffold_override_enables_generation(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=False)

    result = runner.invoke(
        app,
        ["gen", "--project-dir", str(tmp_path), "--scaffold", "--baseline-ref", "v1.0.0"],
    )

    assert result.exit_code == 0
    generated_root = tmp_path / ".apidev" / "output" / "api"
    assert (generated_root / "integration" / "handler_registry.py").exists()
    assert (generated_root / "integration" / "router_factory.py").exists()
    assert (generated_root / "integration" / "auth_registry.py").exists()
    assert (generated_root / "integration" / "error_mapper.py").exists()


def test_diff_cli_scaffold_override_is_accepted(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=False)

    result = runner.invoke(app, ["diff", "--project-dir", str(tmp_path), "--scaffold"])

    assert result.exit_code == 0
    assert "Drift status: drift" in result.output


def test_gen_preserves_existing_scaffold_file(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True)
    _run_generate(tmp_path)

    scaffold_file = tmp_path / ".apidev" / "output" / "api" / "integration" / "handler_registry.py"
    sentinel = "# user-owned scaffold\n"
    scaffold_file.write_text(sentinel, encoding="utf-8")

    _run_generate(tmp_path)

    assert scaffold_file.read_text(encoding="utf-8") == sentinel


def test_gen_rejects_mutually_exclusive_scaffold_flags(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True)

    result = runner.invoke(
        app,
        ["gen", "--project-dir", str(tmp_path), "--scaffold", "--no-scaffold"],
    )

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output.lower()


def test_gen_preserves_custom_scaffold_python_file_when_scaffold_enabled(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True)
    _run_generate(tmp_path)

    custom_scaffold = tmp_path / ".apidev" / "output" / "api" / "integration" / "custom_handler.py"
    sentinel = "# custom scaffold\n"
    custom_scaffold.write_text(sentinel, encoding="utf-8")

    _run_generate(tmp_path)

    assert custom_scaffold.exists()
    assert custom_scaffold.read_text(encoding="utf-8") == sentinel


def test_gen_cli_no_scaffold_override_removes_existing_scaffold_files(tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True)
    _run_generate(tmp_path)

    generated_root = tmp_path / ".apidev" / "output" / "api"
    custom_scaffold = generated_root / "integration" / "custom_handler.py"
    custom_scaffold.write_text("# stale scaffold\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["gen", "--project-dir", str(tmp_path), "--no-scaffold", "--baseline-ref", "v1.0.0"],
    )

    assert result.exit_code == 0
    assert not custom_scaffold.exists()
