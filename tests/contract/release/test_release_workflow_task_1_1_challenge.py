from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

_TARGET_FILE = Path(__file__).with_name("test_release_workflow_task_1_1.py")
_TARGET_SPEC = importlib.util.spec_from_file_location("release_task_1_1", _TARGET_FILE)
assert _TARGET_SPEC is not None and _TARGET_SPEC.loader is not None
target = importlib.util.module_from_spec(_TARGET_SPEC)
_TARGET_SPEC.loader.exec_module(target)


def _write_release_workflow(tmp_path: Path, workflow_data: dict) -> None:
    workflow_path = tmp_path / ".github" / "workflows" / "release.yml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(
        yaml.safe_dump(workflow_data, sort_keys=False),
        encoding="utf-8",
    )


def test_load_fails_when_release_workflow_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(AssertionError, match="Expected baseline release workflow"):
        target._load_release_workflow()


def test_manual_trigger_rejects_null_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_release_workflow(
        tmp_path,
        {
            "name": "release",
            "on": {
                "release": {"types": ["published"]},
                "workflow_dispatch": None,
            },
            "jobs": {
                "release": {
                    "strategy": {
                        "matrix": {
                            "os": [
                                "ubuntu-latest",
                                "macos-latest",
                                "windows-latest",
                            ]
                        }
                    }
                }
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        AssertionError, match="Manual trigger 'workflow_dispatch' must be an explicit mapping"
    ):
        target.test_release_workflow_has_required_triggers()


def test_matrix_rejects_empty_os_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_release_workflow(
        tmp_path,
        {
            "name": "release",
            "on": {
                "release": {"types": ["published"]},
                "workflow_dispatch": {},
            },
            "jobs": {
                "release": {
                    "strategy": {
                        "matrix": {
                            "os": [],
                        }
                    }
                }
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        AssertionError, match="Matrix must cover Linux/macOS/Windows in deterministic order"
    ):
        target.test_release_workflow_has_multi_os_matrix_targets()
