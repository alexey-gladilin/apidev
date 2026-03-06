from pathlib import Path

from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.testing.config_helpers import (
    DEFAULT_RELEASE_STATE_RELATIVE_PATH,
    write_config,
    write_release_state,
)

VALID_RELEASE_STATE_PAYLOAD = {"release_number": 3, "baseline_ref": "v1.2.3"}


def test_load_release_state_uses_default_path_when_release_state_file_omitted(
    tmp_path: Path,
) -> None:
    write_config(tmp_path, "")
    write_release_state(tmp_path, VALID_RELEASE_STATE_PAYLOAD)

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)
    release_state = loader.load_release_state(tmp_path, config)

    assert release_state.release_number == 3
    assert release_state.baseline_ref == "v1.2.3"


def test_load_release_state_accepts_normalized_relative_path_within_project(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[evolution]
release_state_file = ".apidev/../.apidev/release-state.json"
""",
    )
    write_release_state(
        tmp_path,
        VALID_RELEASE_STATE_PAYLOAD,
        relative_path=DEFAULT_RELEASE_STATE_RELATIVE_PATH,
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)
    release_state = loader.load_release_state(tmp_path, config)

    assert release_state.release_number == 3
    assert release_state.baseline_ref == "v1.2.3"
