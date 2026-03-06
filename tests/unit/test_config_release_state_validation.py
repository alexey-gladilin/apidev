from pathlib import Path
import json

import pytest

from apidev.core.constants import DEFAULT_RELEASE_STATE_FILE
from apidev.core.constants import (
    DIAG_CODE_PATH_BOUNDARY_VIOLATION,
    DIAG_CODE_RELEASE_STATE_INVALID_KEY,
    DIAG_CODE_RELEASE_STATE_TYPE_MISMATCH,
    DIAG_FIELD_ERROR_CODE,
    DIAG_FIELD_KEY_PATH,
    DIAG_FIELD_PROJECT_DIR,
    DIAG_FIELD_RESOLVED_PATH,
    DIAG_KEY_PATH_EVOLUTION_RELEASE_STATE_FILE,
)
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.testing.config_helpers import (
    APIDEV_DIRNAME,
    write_config,
    write_release_state,
)

DEFAULT_RELEASE_STATE_LINE = f'release_state_file = "{DEFAULT_RELEASE_STATE_FILE}"'
DEFAULT_RELEASE_STATE_PATH = Path(DEFAULT_RELEASE_STATE_FILE)
DEFAULT_EVOLUTION_CONFIG = f"""
[evolution]
{DEFAULT_RELEASE_STATE_LINE}
"""
BASELINE_REF = "v1.0.0"
RELEASE_STATE_V1_PAYLOAD = {"release_number": 1, "baseline_ref": BASELINE_REF}
LEGACY_CURRENT_RELEASE_PAYLOAD = {"current_release": 2, "baseline_ref": BASELINE_REF}
TYPE_MISMATCH_RELEASE_NUMBER_PAYLOAD = {"release_number": "2", "baseline_ref": BASELINE_REF}


def _extract_error_payload(exc_info: pytest.ExceptionInfo[ValueError]) -> dict[str, str]:
    payload = json.loads(str(exc_info.value))
    assert isinstance(payload, dict)
    return payload


def _expected_path_boundary_payload(tmp_path: Path, resolved_path: Path) -> dict[str, str]:
    return {
        DIAG_FIELD_ERROR_CODE: DIAG_CODE_PATH_BOUNDARY_VIOLATION,
        DIAG_FIELD_KEY_PATH: DIAG_KEY_PATH_EVOLUTION_RELEASE_STATE_FILE,
        DIAG_FIELD_PROJECT_DIR: tmp_path.resolve().as_posix(),
        DIAG_FIELD_RESOLVED_PATH: resolved_path.resolve().as_posix(),
    }


def test_config_rejects_grace_period_less_than_one(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[evolution]
grace_period_releases = 0
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError, match=r"evolution\.grace_period_releases"):
        loader.load(tmp_path)


def test_config_rejects_blank_release_state_file(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[evolution]
release_state_file = "   "
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError, match=r"evolution\.release_state_file"):
        loader.load(tmp_path)


def test_release_state_rejects_missing_baseline_ref(tmp_path: Path) -> None:
    write_config(tmp_path, DEFAULT_EVOLUTION_CONFIG)
    write_release_state(tmp_path, {"release_number": 2})

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"baseline_ref"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_invalid_baseline_ref_format(tmp_path: Path) -> None:
    write_config(tmp_path, DEFAULT_EVOLUTION_CONFIG)
    write_release_state(tmp_path, {"release_number": 2, "baseline_ref": "bad ref"})

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"baseline_ref"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_absolute_path(tmp_path: Path) -> None:
    outside = tmp_path / "absolute-release-state.json"
    write_release_state(tmp_path, RELEASE_STATE_V1_PAYLOAD, relative_path=Path(outside.name))
    write_config(
        tmp_path,
        f"""
[evolution]
release_state_file = "{outside}"
""",
    )
    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        loader.load_release_state(tmp_path, config)

    payload = _extract_error_payload(exc_info)
    assert payload == _expected_path_boundary_payload(tmp_path, outside)


def test_release_state_rejects_traversal_outside_project(tmp_path: Path) -> None:
    escaped = tmp_path.parent / "escaped-release-state.json"
    escaped.write_text(json.dumps(RELEASE_STATE_V1_PAYLOAD), encoding="utf-8")
    write_config(
        tmp_path,
        """
[evolution]
release_state_file = "../escaped-release-state.json"
""",
    )
    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        loader.load_release_state(tmp_path, config)

    payload = _extract_error_payload(exc_info)
    assert payload == _expected_path_boundary_payload(tmp_path, escaped)


def test_release_state_rejects_symlink_escape(tmp_path: Path) -> None:
    escaped = tmp_path.parent / "symlink-escaped-release-state.json"
    escaped.write_text(json.dumps(RELEASE_STATE_V1_PAYLOAD), encoding="utf-8")
    link = tmp_path / APIDEV_DIRNAME / "release-link.json"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(escaped)
    write_config(
        tmp_path,
        """
[evolution]
release_state_file = ".apidev/release-link.json"
""",
    )
    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        loader.load_release_state(tmp_path, config)

    payload = _extract_error_payload(exc_info)
    assert payload == _expected_path_boundary_payload(tmp_path, escaped)


def test_release_state_rejects_oversize_file(tmp_path: Path) -> None:
    oversized_baseline = "v" + ("x" * (2 * 1024 * 1024))
    payload = '{"release_number": 1, "baseline_ref": "' + oversized_baseline + '"}'
    write_config(tmp_path, DEFAULT_EVOLUTION_CONFIG)
    (tmp_path / DEFAULT_RELEASE_STATE_PATH).write_text(payload, encoding="utf-8")

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"exceeds max size"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_legacy_current_release_key_with_diagnostics_payload(
    tmp_path: Path,
) -> None:
    write_config(tmp_path, DEFAULT_EVOLUTION_CONFIG)
    write_release_state(
        tmp_path,
        LEGACY_CURRENT_RELEASE_PAYLOAD,
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        loader.load_release_state(tmp_path, config)

    payload = json.loads(str(exc_info.value))
    assert payload["code"] == DIAG_CODE_RELEASE_STATE_INVALID_KEY
    assert payload["message"] == "release-state contains unsupported legacy key"
    assert payload["context"] == {"field": "current_release"}


def test_release_state_rejects_release_number_type_mismatch_with_diagnostics_payload(
    tmp_path: Path,
) -> None:
    write_config(tmp_path, DEFAULT_EVOLUTION_CONFIG)
    write_release_state(
        tmp_path,
        TYPE_MISMATCH_RELEASE_NUMBER_PAYLOAD,
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        loader.load_release_state(tmp_path, config)

    payload = json.loads(str(exc_info.value))
    assert payload["code"] == DIAG_CODE_RELEASE_STATE_TYPE_MISMATCH
    assert payload["message"] == "release-state field has invalid type"
    assert payload["context"] == {
        "actual_type": "str",
        "expected_type": "int",
        "field": "release_number",
    }


def test_config_rejects_legacy_version_key_with_deterministic_key_path(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
version = "1"
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError) as exc_info:
        loader.load(tmp_path)

    assert "key_path=version" in str(exc_info.value)


def test_config_rejects_legacy_contracts_and_templates_with_deterministic_key_paths(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        """
[contracts]
dir = "legacy/contracts"
shared_models_dir = "legacy/models"

[templates]
dir = "legacy/templates"
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError) as exc_info:
        loader.load(tmp_path)

    message = str(exc_info.value)
    assert "key_path=contracts" in message
    assert "key_path=templates" in message


def test_config_rejects_unknown_key_with_key_path(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[generator]
unknown = true
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError) as exc_info:
        loader.load(tmp_path)

    message = str(exc_info.value)
    assert "generator.unknown" in message
