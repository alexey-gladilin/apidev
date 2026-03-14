from pathlib import Path
import tomllib

from typer.testing import CliRunner

from apidev.cli import app
from apidev.testing.constants import CANONICAL_TOP_LEVEL_CONFIG_KEYS

runner = CliRunner()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _template_path(project_dir: Path, template_name: str) -> Path:
    return project_dir / ".apidev" / "templates" / template_name


def test_init_and_integration_create_scaffold_fastapi_scope(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--runtime",
            "fastapi",
            "--integration-mode",
            "scaffold",
        ],
    )

    assert result.exit_code == 0
    assert _template_path(tmp_path, "integration_handler_registry.py.j2").exists()
    assert _template_path(tmp_path, "integration_error_mapper.py.j2").exists()
    assert _template_path(tmp_path, "integration_router_factory.py.j2").exists()
    assert _template_path(tmp_path, "integration_auth_registry.py.j2").exists()
    assert not _template_path(tmp_path, "generated_operation_map.py.j2").exists()
    assert not _template_path(tmp_path, "generated_openapi_docs.py.j2").exists()


def test_init_bootstrap_contracts_validate_with_shared_model_refs(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["init", "--project-dir", str(tmp_path)])

    assert init_result.exit_code == 0
    assert _template_path(tmp_path, "generated_operation_map.py.j2").exists()
    assert _template_path(tmp_path, "generated_openapi_docs.py.j2").exists()
    assert _template_path(tmp_path, "generated_router.py.j2").exists()
    assert _template_path(tmp_path, "generated_schema.py.j2").exists()

    validate_result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path)])

    assert validate_result.exit_code == 0
    assert "Contracts valid." in validate_result.output


def test_init_and_integration_create_scaffold_runtime_none_scope(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--runtime",
            "none",
            "--integration-mode",
            "scaffold",
        ],
    )

    assert result.exit_code == 0
    assert _template_path(tmp_path, "integration_handler_registry.py.j2").exists()
    assert _template_path(tmp_path, "integration_error_mapper.py.j2").exists()
    assert not _template_path(tmp_path, "integration_router_factory.py.j2").exists()
    assert not _template_path(tmp_path, "integration_auth_registry.py.j2").exists()


def test_init_and_integration_repair_restores_only_profile_managed_templates(
    tmp_path: Path,
) -> None:
    first = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--runtime",
            "fastapi",
            "--integration-mode",
            "full",
        ],
    )
    assert first.exit_code == 0

    target = _template_path(tmp_path, "integration_handler_registry.py.j2")
    original = _read(target)
    target.write_text("# broken by user\n", encoding="utf-8")

    create_result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--runtime",
            "fastapi",
            "--integration-mode",
            "full",
        ],
    )
    assert create_result.exit_code == 1
    assert "--repair" in create_result.output
    assert "--force" in create_result.output

    repair_result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--repair",
            "--runtime",
            "fastapi",
            "--integration-mode",
            "full",
        ],
    )

    assert repair_result.exit_code == 0
    assert _read(target) == original


def test_init_and_integration_force_overwrites_profile_scope(tmp_path: Path) -> None:
    first = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--runtime",
            "fastapi",
            "--integration-mode",
            "full",
        ],
    )
    assert first.exit_code == 0

    operation_map_template = _template_path(tmp_path, "generated_operation_map.py.j2")
    original = _read(operation_map_template)
    operation_map_template.write_text("# modified\n", encoding="utf-8")

    force_result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--force",
            "--runtime",
            "fastapi",
            "--integration-mode",
            "full",
        ],
    )

    assert force_result.exit_code == 0
    assert _read(operation_map_template) == original


def test_init_and_integration_off_mode_skips_template_bootstrap(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--runtime",
            "fastapi",
            "--integration-mode",
            "off",
        ],
    )

    assert result.exit_code == 0
    assert not _template_path(tmp_path, "integration_handler_registry.py.j2").exists()
    assert not _template_path(tmp_path, "integration_error_mapper.py.j2").exists()
    assert not _template_path(tmp_path, "integration_router_factory.py.j2").exists()
    assert not _template_path(tmp_path, "integration_auth_registry.py.j2").exists()
    assert not _template_path(tmp_path, "generated_operation_map.py.j2").exists()
    assert not _template_path(tmp_path, "generated_openapi_docs.py.j2").exists()


def test_init_and_integration_repair_rejects_outside_contracts_dir(tmp_path: Path) -> None:
    first = runner.invoke(app, ["init", "--project-dir", str(tmp_path)])
    assert first.exit_code == 0

    (tmp_path / ".apidev" / "config.toml").write_text(
        """[inputs]
contracts_dir = "../contracts-outside"
[generator]
generated_dir = ".apidev/output/api"
[paths]
templates_dir = ".apidev/templates"
""".strip() + "\n",
        encoding="utf-8",
    )

    repair_result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--repair",
        ],
    )

    assert repair_result.exit_code != 0
    assert "validation.PATH_BOUNDARY_VIOLATION" in repair_result.output


def test_init_and_integration_force_rejects_absolute_templates_dir(tmp_path: Path) -> None:
    first = runner.invoke(app, ["init", "--project-dir", str(tmp_path)])
    assert first.exit_code == 0

    absolute_templates_dir = (tmp_path.parent / "templates-outside-absolute").resolve()
    (tmp_path / ".apidev" / "config.toml").write_text(
        f"""[inputs]
contracts_dir = ".apidev/contracts"
[generator]
generated_dir = ".apidev/output/api"
[paths]
templates_dir = "{absolute_templates_dir}"
""".strip() + "\n",
        encoding="utf-8",
    )

    force_result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--force",
        ],
    )

    assert force_result.exit_code != 0
    assert "validation.PATH_BOUNDARY_VIOLATION" in force_result.output


def test_init_materializes_only_canonical_config_format(
    tmp_path: Path,
    monkeypatch,
) -> None:
    legacy_default_config = """
version = 1
templates_dir = ".apidev/templates"
contracts_dir = ".apidev/contracts"
generated_dir = ".apidev/output/api"
""".strip()

    monkeypatch.setattr(
        "apidev.infrastructure.config.toml_loader.default_config_text",
        lambda: legacy_default_config,
    )

    result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--integration-dir",
            "platform/integration",
        ],
    )

    assert result.exit_code == 0

    config_data = tomllib.loads((tmp_path / ".apidev" / "config.toml").read_text(encoding="utf-8"))
    assert set(config_data.keys()) == CANONICAL_TOP_LEVEL_CONFIG_KEYS
    assert "version" not in config_data
    assert "templates_dir" not in config_data
    assert "contracts_dir" not in config_data
    assert "generated_dir" not in config_data
    assert config_data["generator"]["scaffold_dir"] == "platform/integration"
