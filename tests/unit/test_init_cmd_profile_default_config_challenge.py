from __future__ import annotations

from pathlib import Path
import tomllib

import pytest
import typer

from apidev.commands.init_cmd import _profile_default_config_text, _validate_integration_dir
from apidev.testing.constants import CANONICAL_TOP_LEVEL_CONFIG_KEYS


def test_profile_default_config_empty_input_falls_back_to_canonical_format() -> None:
    rendered = _profile_default_config_text(base_text="", integration_dir="custom/integration")
    parsed = tomllib.loads(rendered)

    assert set(parsed.keys()) == CANONICAL_TOP_LEVEL_CONFIG_KEYS
    assert parsed["generator"]["scaffold_dir"] == "custom/integration"


def test_profile_default_config_malformed_toml_falls_back_to_canonical_format() -> None:
    rendered = _profile_default_config_text(
        base_text='invalid = "unterminated',
        integration_dir="platform/gateway",
    )
    parsed = tomllib.loads(rendered)

    assert set(parsed.keys()) == CANONICAL_TOP_LEVEL_CONFIG_KEYS
    assert parsed["generator"]["scaffold_dir"] == "platform/gateway"


def test_validate_integration_dir_rejects_none_input(tmp_path: Path) -> None:
    with pytest.raises(typer.BadParameter, match="validation.PATH_BOUNDARY_VIOLATION"):
        _validate_integration_dir(project_root=tmp_path, integration_dir=None)
