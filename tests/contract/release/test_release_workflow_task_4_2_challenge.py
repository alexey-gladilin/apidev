from __future__ import annotations

from pathlib import Path

import pytest
from typer import BadParameter
from typer.testing import CliRunner

from apidev.cli import app
from apidev.commands.init_cmd import _validate_integration_dir

runner = CliRunner()


def test_init_rejects_empty_integration_dir_input(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["init", "--project-dir", str(tmp_path), "--integration-dir", ""],
    )

    assert result.exit_code != 0
    assert "validation.PATH_BOUNDARY_VIOLATION" in result.output


def test_validate_integration_dir_rejects_none_value(tmp_path: Path) -> None:
    with pytest.raises(BadParameter, match="validation.PATH_BOUNDARY_VIOLATION"):
        _validate_integration_dir(project_root=tmp_path.resolve(), integration_dir=None)


def test_init_rejects_integration_dir_path_escape(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["init", "--project-dir", str(tmp_path), "--integration-dir", "../outside"],
    )

    assert result.exit_code != 0
    assert "validation.PATH_BOUNDARY_VIOLATION" in result.output
