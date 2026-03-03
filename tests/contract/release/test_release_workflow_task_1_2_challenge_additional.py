from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

_TARGET_FILE = Path(__file__).with_name("test_release_workflow_task_1_2.py")
_TARGET_SPEC = importlib.util.spec_from_file_location("release_task_1_2", _TARGET_FILE)
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


def test_release_workflow_rejects_null_jobs_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_release_workflow(
        tmp_path,
        {
            "name": "release",
            "on": {"release": {"types": ["published"]}, "workflow_dispatch": {}},
            "jobs": None,
        },
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(AssertionError, match="Workflow must define jobs"):
        target._get_release_job_steps()


def test_release_workflow_rejects_empty_steps_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_release_workflow(
        tmp_path,
        {
            "name": "release",
            "on": {"release": {"types": ["published"]}, "workflow_dispatch": {}},
            "jobs": {"release": {"steps": []}},
        },
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        AssertionError, match="Missing required step 'Install release build dependencies'"
    ):
        target.test_release_workflow_has_build_smoke_package_steps_in_order()
