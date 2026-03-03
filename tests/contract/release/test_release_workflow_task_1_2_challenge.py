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


def _write_makefile(tmp_path: Path, body: str) -> None:
    (tmp_path / "Makefile").write_text(body, encoding="utf-8")


def test_release_step_order_rejects_package_before_smoke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_release_workflow(
        tmp_path,
        {
            "name": "release",
            "on": {"release": {"types": ["published"]}, "workflow_dispatch": {}},
            "jobs": {
                "release": {
                    "steps": [
                        {
                            "name": "Install release build dependencies",
                            "run": "python -m pip install .",
                        },
                        {
                            "name": "Build standalone binary",
                            "run": "python scripts/release/build_binary.py",
                        },
                        {
                            "name": "Package standalone binary",
                            "run": "python scripts/release/package_binary.py",
                        },
                        {
                            "name": "Smoke check standalone binary",
                            "run": "python scripts/release/smoke_binary.py",
                        },
                    ]
                }
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        AssertionError,
        match="Release job must execute install -> build -> smoke -> package in order",
    ):
        target.test_release_workflow_has_build_smoke_package_steps_in_order()


def test_smoke_gate_contract_rejects_missing_help_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripts_dir = tmp_path / "scripts" / "release"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "smoke_binary.py").write_text(
        'print("smoke without help")\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(AssertionError, match="Smoke helper script must enforce apidev --help gate"):
        target.test_smoke_script_contains_apidev_help_gate()


def test_makefile_contract_rejects_missing_release_package_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_makefile(
        tmp_path,
        "\n".join(
            [
                "release-build:",
                '\t@echo "build"',
                "release-smoke:",
                '\t@echo "smoke"',
            ]
        )
        + "\n",
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(AssertionError, match="Makefile must define 'release-package' target"):
        target.test_makefile_exposes_release_build_smoke_package_targets()
