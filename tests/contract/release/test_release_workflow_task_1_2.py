from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import yaml


def _load_release_workflow() -> dict:
    workflow_path = Path(".github/workflows/release.yml")
    assert workflow_path.exists(), (
        "Expected release workflow at .github/workflows/release.yml for task 1.2"
    )
    with workflow_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    assert isinstance(data, dict), "Workflow YAML must be a mapping"
    return data


def _get_release_job_steps() -> list[dict]:
    workflow = _load_release_workflow()
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs"

    release_job = jobs.get("release")
    assert isinstance(release_job, dict), "Workflow must define 'release' job"

    steps = release_job.get("steps")
    assert isinstance(steps, list), "'release' job must define steps list"
    return steps


def _find_step(steps: list[dict], step_name: str) -> tuple[int, dict]:
    for index, step in enumerate(steps):
        if isinstance(step, dict) and step.get("name") == step_name:
            return index, step
    raise AssertionError(f"Missing required step '{step_name}' in release job")


def test_release_workflow_has_build_smoke_package_steps_in_order() -> None:
    steps = _get_release_job_steps()

    install_index, _ = _find_step(steps, "Install release build dependencies")
    build_index, _ = _find_step(steps, "Build standalone binary")
    smoke_index, _ = _find_step(steps, "Smoke check standalone binary")
    package_index, _ = _find_step(steps, "Package standalone binary")

    assert install_index < build_index < smoke_index < package_index, (
        "Release job must execute install -> build -> smoke -> package in order"
    )


def test_release_workflow_wires_release_scripts_for_core_steps() -> None:
    steps = _get_release_job_steps()

    _, build_step = _find_step(steps, "Build standalone binary")
    _, smoke_step = _find_step(steps, "Smoke check standalone binary")
    _, package_step = _find_step(steps, "Package standalone binary")

    build_run = build_step.get("run")
    smoke_run = smoke_step.get("run")
    package_run = package_step.get("run")
    assert isinstance(build_run, str), "Build step must define run command"
    assert isinstance(smoke_run, str), "Smoke step must define run command"
    assert isinstance(package_run, str), "Package step must define run command"

    assert "scripts/release/build_binary.py" in build_run, (
        "Build step must call scripts/release/build_binary.py"
    )
    assert "scripts/release/smoke_binary.py" in smoke_run, (
        "Smoke step must call scripts/release/smoke_binary.py"
    )
    assert "scripts/release/package_binary.py" in package_run, (
        "Package step must call scripts/release/package_binary.py"
    )


def test_release_helper_scripts_exist_for_task_1_2_scope() -> None:
    release_scripts = [
        Path("scripts/release/build_binary.py"),
        Path("scripts/release/smoke_binary.py"),
        Path("scripts/release/package_binary.py"),
    ]
    for script_path in release_scripts:
        assert script_path.exists(), f"Expected release helper script: {script_path}"


def test_smoke_script_contains_apidev_help_gate() -> None:
    smoke_script = Path("scripts/release/smoke_binary.py")
    assert smoke_script.exists(), (
        "Smoke helper script must exist at scripts/release/smoke_binary.py"
    )
    content = smoke_script.read_text(encoding="utf-8")
    assert "apidev" in content and "--help" in content, (
        "Smoke helper script must enforce apidev --help gate"
    )


def test_makefile_exposes_release_build_smoke_package_targets() -> None:
    makefile_path = Path("Makefile")
    assert makefile_path.exists(), "Expected Makefile in project root"
    content = makefile_path.read_text(encoding="utf-8")

    assert "release-build:" in content, "Makefile must define 'release-build' target"
    assert "release-smoke:" in content, "Makefile must define 'release-smoke' target"
    assert "release-package:" in content, "Makefile must define 'release-package' target"


def test_makefile_release_package_passes_runner_metadata() -> None:
    makefile_path = Path("Makefile")
    assert makefile_path.exists(), "Expected Makefile in project root"
    content = makefile_path.read_text(encoding="utf-8")

    assert "--runner-os" in content, (
        "Makefile release-package target must pass --runner-os to package script"
    )
    assert "--runner-arch" in content, (
        "Makefile release-package target must pass --runner-arch to package script"
    )


def test_release_workflow_pins_setup_python_action_to_full_commit_sha() -> None:
    steps = _get_release_job_steps()
    _, setup_python_step = _find_step(steps, "Setup Python")

    uses = setup_python_step.get("uses")
    assert isinstance(uses, str), "Setup Python step must define 'uses' as a string"
    assert uses.startswith("actions/setup-python@"), (
        "Setup Python step must use actions/setup-python"
    )

    setup_python_ref = uses.split("@", 1)[1]
    assert len(setup_python_ref) == 40 and all(
        char in "0123456789abcdef" for char in setup_python_ref
    ), "Setup Python action must be pinned to immutable full 40-char lowercase commit SHA"


def test_release_workflow_uses_locked_release_dependency_install_path() -> None:
    steps = _get_release_job_steps()
    _, install_step = _find_step(steps, "Install release build dependencies")

    install_run = install_step.get("run")
    assert isinstance(install_run, str), "Install step must define run command"
    assert "python -m pip install -r requirements/code.txt" in install_run, (
        "Release install step must install locked dependencies from requirements/code.txt"
    )
    assert "python -m pip install --no-deps ." in install_run, (
        "Release install step must install project artifact with --no-deps"
    )
    assert not re.search(r"pip install\s+\.(?:\s|$)", install_run), (
        "Release install step must not use plain 'pip install .' with floating dependencies"
    )


def _load_package_binary_module():
    module_path = Path("scripts/release/package_binary.py")
    spec = importlib.util.spec_from_file_location("package_binary", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_binary_archive_name_allowlist_happy_path() -> None:
    module = _load_package_binary_module()

    assert (
        module._resolve_archive_name("Linux", "X64", None) == "apidev-linux-x64.tar.gz"
    )
    assert (
        module._resolve_archive_name("Windows", "ARM64", None)
        == "apidev-windows-arm64.zip"
    )


def test_package_binary_archive_name_allowlist_rejects_invalid_runner_inputs() -> None:
    module = _load_package_binary_module()

    try:
        module._resolve_archive_name("linux;rm -rf /", "x64", None)
        raise AssertionError("Expected ValueError for invalid runner_os")
    except ValueError as error:
        assert "runner_os" in str(error)

    try:
        module._resolve_archive_name("linux", "x64/../../", None)
        raise AssertionError("Expected ValueError for invalid runner_arch")
    except ValueError as error:
        assert "runner_arch" in str(error)


def test_package_binary_archive_name_override_validation_rejects_path_traversal() -> None:
    module = _load_package_binary_module()

    try:
        module._resolve_archive_name("linux", "x64", "../evil.tar.gz")
        raise AssertionError("Expected ValueError for unsafe archive_name override")
    except ValueError as error:
        assert "archive_name" in str(error)


def test_package_binary_main_defaults_runner_arch_when_env_missing(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_package_binary_module()
    binary_path = tmp_path / "apidev"
    binary_path.write_bytes(b"binary")
    output_dir = tmp_path / "release"

    monkeypatch.setenv("RUNNER_OS", "linux")
    monkeypatch.delenv("RUNNER_ARCH", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "package_binary.py",
            "--binary-path",
            str(binary_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    result = module.main()

    archives = list(output_dir.glob("apidev-linux-*"))
    assert result == 0, "Package script should succeed without RUNNER_ARCH env"
    assert archives, "Package script should emit a release archive when RUNNER_ARCH is absent"
