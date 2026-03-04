from pathlib import Path
import json

import pytest

from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


def _write_config(project_dir: Path, toml_text: str) -> None:
    (project_dir / ".apidev").mkdir(parents=True, exist_ok=True)
    (project_dir / ".apidev" / "config.toml").write_text(toml_text.strip() + "\n", encoding="utf-8")


def test_config_rejects_grace_period_less_than_one(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"

[evolution]
grace_period_releases = 0
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError, match=r"evolution\.grace_period_releases"):
        loader.load(tmp_path)


def test_config_rejects_blank_release_state_file(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"

[evolution]
release_state_file = "   "
""",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())

    with pytest.raises(ValueError, match=r"evolution\.release_state_file"):
        loader.load(tmp_path)


def test_release_state_rejects_missing_baseline_ref(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        """
version = "1"

[evolution]
release_state_file = ".apidev/release-state.json"
""",
    )
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number": 2}',
        encoding="utf-8",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"baseline_ref"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_invalid_baseline_ref_format(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        """
version = "1"

[evolution]
release_state_file = ".apidev/release-state.json"
""",
    )
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number": 2, "baseline_ref": "bad ref"}',
        encoding="utf-8",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"baseline_ref"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_absolute_path(tmp_path: Path) -> None:
    outside = tmp_path / "absolute-release-state.json"
    outside.write_text(
        '{"release_number": 1, "baseline_ref": "v1.0.0"}',
        encoding="utf-8",
    )
    _write_config(
        tmp_path,
        f"""
version = "1"

[evolution]
release_state_file = "{outside}"
""",
    )
    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"absolute paths are not allowed"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_traversal_outside_project(tmp_path: Path) -> None:
    escaped = tmp_path.parent / "escaped-release-state.json"
    escaped.write_text(
        '{"release_number": 1, "baseline_ref": "v1.0.0"}',
        encoding="utf-8",
    )
    _write_config(
        tmp_path,
        """
version = "1"

[evolution]
release_state_file = "../escaped-release-state.json"
""",
    )
    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"must stay inside project directory"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_symlink_escape(tmp_path: Path) -> None:
    escaped = tmp_path.parent / "symlink-escaped-release-state.json"
    escaped.write_text(
        '{"release_number": 1, "baseline_ref": "v1.0.0"}',
        encoding="utf-8",
    )
    link = tmp_path / ".apidev" / "release-link.json"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(escaped)
    _write_config(
        tmp_path,
        """
version = "1"

[evolution]
release_state_file = ".apidev/release-link.json"
""",
    )
    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"must stay inside project directory"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_oversize_file(tmp_path: Path) -> None:
    oversized_baseline = "v" + ("x" * (2 * 1024 * 1024))
    payload = '{"release_number": 1, "baseline_ref": "' + oversized_baseline + '"}'
    _write_config(
        tmp_path,
        """
version = "1"

[evolution]
release_state_file = ".apidev/release-state.json"
""",
    )
    (tmp_path / ".apidev" / "release-state.json").write_text(payload, encoding="utf-8")

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError, match=r"exceeds max size"):
        loader.load_release_state(tmp_path, config)


def test_release_state_rejects_legacy_current_release_key_with_diagnostics_payload(
    tmp_path: Path,
) -> None:
    _write_config(
        tmp_path,
        """
version = "1"

[evolution]
release_state_file = ".apidev/release-state.json"
""",
    )
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"current_release": 2, "baseline_ref": "v1.0.0"}',
        encoding="utf-8",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        loader.load_release_state(tmp_path, config)

    payload = json.loads(str(exc_info.value))
    assert payload["code"] == "validation.RELEASE_STATE_INVALID_KEY"
    assert payload["message"] == "release-state contains unsupported legacy key"
    assert payload["context"] == {"field": "current_release"}


def test_release_state_rejects_release_number_type_mismatch_with_diagnostics_payload(
    tmp_path: Path,
) -> None:
    _write_config(
        tmp_path,
        """
version = "1"

[evolution]
release_state_file = ".apidev/release-state.json"
""",
    )
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number": "2", "baseline_ref": "v1.0.0"}',
        encoding="utf-8",
    )

    loader = TomlConfigLoader(fs=LocalFileSystem())
    config = loader.load(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        loader.load_release_state(tmp_path, config)

    payload = json.loads(str(exc_info.value))
    assert payload["code"] == "validation.RELEASE_STATE_TYPE_MISMATCH"
    assert payload["message"] == "release-state field has invalid type"
    assert payload["context"] == {
        "actual_type": "str",
        "expected_type": "int",
        "field": "release_number",
    }
