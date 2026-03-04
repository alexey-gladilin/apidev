from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _assert_scaffold_outputs(root: Path) -> None:
    assert (root / "handler_registry.py").exists()
    assert (root / "router_factory.py").exists()
    assert (root / "auth_registry.py").exists()
    assert (root / "error_mapper.py").exists()


def test_init_and_gen_pipeline_uses_custom_integration_dir_from_profile(tmp_path: Path) -> None:
    custom_integration_dir = "platform/integration"
    init_result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--runtime",
            "fastapi",
            "--integration-mode",
            "scaffold",
            "--integration-dir",
            custom_integration_dir,
        ],
    )
    assert init_result.exit_code == 0

    gen_result = runner.invoke(
        app,
        ["gen", "--project-dir", str(tmp_path), "--baseline-ref", "v1.0.0"],
    )
    assert gen_result.exit_code == 0

    custom_scaffold_root = tmp_path / custom_integration_dir
    default_scaffold_root = tmp_path / "integration"
    _assert_scaffold_outputs(custom_scaffold_root)
    assert not (default_scaffold_root / "handler_registry.py").exists()
