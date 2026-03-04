from pathlib import Path

import pytest

from apidev.core.models.config import ApidevConfig
from apidev.infrastructure.config.toml_loader import default_config_text


def test_config_model_sets_scaffold_defaults() -> None:
    config = ApidevConfig()

    assert config.generator.scaffold is True
    assert config.generator.scaffold_dir == "integration"
    assert config.generator.scaffold_write_policy == "create-missing"
    assert config.openapi.include_extensions is True


def test_default_config_text_contains_scaffold_defaults() -> None:
    text = default_config_text()

    assert "scaffold = true" in text
    assert 'scaffold_dir = "integration"' in text
    assert 'scaffold_write_policy = "create-missing"' in text
    assert "[openapi]" in text
    assert "include_extensions = true" in text


def test_config_allows_disabling_openapi_extensions() -> None:
    config = ApidevConfig.model_validate({"openapi": {"include_extensions": False}})

    assert config.openapi.include_extensions is False


def test_config_rejects_empty_generated_dir() -> None:
    with pytest.raises(ValueError, match="generated_dir"):
        ApidevConfig.model_validate({"generator": {"generated_dir": "   "}})


def test_config_rejects_absolute_scaffold_dir() -> None:
    absolute = str((Path.cwd() / "scaffold").resolve())
    with pytest.raises(ValueError, match="scaffold_dir"):
        ApidevConfig.model_validate({"generator": {"scaffold_dir": absolute}})


def test_config_rejects_absolute_generated_dir() -> None:
    absolute = str((Path.cwd() / "generated").resolve())
    with pytest.raises(ValueError, match="generated_dir"):
        ApidevConfig.model_validate({"generator": {"generated_dir": absolute}})


def test_config_accepts_supported_scaffold_write_policies() -> None:
    for policy in ("create-missing", "skip-existing", "fail-on-conflict"):
        config = ApidevConfig.model_validate({"generator": {"scaffold_write_policy": policy}})
        assert config.generator.scaffold_write_policy == policy


def test_config_rejects_unknown_scaffold_write_policy() -> None:
    with pytest.raises(ValueError, match="scaffold_write_policy"):
        ApidevConfig.model_validate({"generator": {"scaffold_write_policy": "overwrite"}})
