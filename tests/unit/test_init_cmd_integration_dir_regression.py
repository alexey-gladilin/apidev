from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _load_scaffold_dir(config_path: Path) -> str:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return str(data["generator"]["scaffold_dir"])


def test_init_create_sets_config_scaffold_dir_from_integration_dir(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--integration-dir",
            "custom/integration",
        ],
    )

    assert result.exit_code == 0
    config_path = tmp_path / ".apidev" / "config.toml"
    assert _load_scaffold_dir(config_path) == "custom/integration"


def test_init_force_rewrites_config_scaffold_dir_from_integration_dir(tmp_path: Path) -> None:
    first = runner.invoke(app, ["init", "--project-dir", str(tmp_path)])
    assert first.exit_code == 0

    result = runner.invoke(
        app,
        [
            "init",
            "--project-dir",
            str(tmp_path),
            "--force",
            "--integration-dir",
            "platform/gateway",
        ],
    )

    assert result.exit_code == 0
    config_path = tmp_path / ".apidev" / "config.toml"
    assert _load_scaffold_dir(config_path) == "platform/gateway"
