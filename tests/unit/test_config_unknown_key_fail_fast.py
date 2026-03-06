from pathlib import Path

import pytest

from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.testing.config_helpers import write_config

KEY_PATH_PREFIX = "key_path="
UNKNOWN_SECTION_KEY_PATHS = ("alpha", "zeta")
UNKNOWN_GENERATOR_KEY_PATHS = ("generator.alpha_key", "generator.zeta_key")


def _extract_key_path_indexes(message: str, key_paths: tuple[str, ...]) -> list[int]:
    return [message.index(f"{KEY_PATH_PREFIX}{key_path}") for key_path in key_paths]


def test_unknown_sections_are_reported_with_stable_sorted_key_paths(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[zeta]
enabled = true

[alpha]
enabled = true
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError) as exc_info:
        loader.load(tmp_path)

    message = str(exc_info.value)
    indexes = _extract_key_path_indexes(message, UNKNOWN_SECTION_KEY_PATHS)
    assert indexes == sorted(indexes)


def test_unknown_keys_are_reported_with_stable_sorted_key_paths(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[generator]
zeta_key = true
alpha_key = true
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError) as exc_info:
        loader.load(tmp_path)

    message = str(exc_info.value)
    indexes = _extract_key_path_indexes(message, UNKNOWN_GENERATOR_KEY_PATHS)
    assert indexes == sorted(indexes)
