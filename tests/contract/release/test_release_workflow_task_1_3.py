from __future__ import annotations

import importlib.util
from pathlib import Path
import re

import yaml


def _load_release_workflow() -> dict:
    workflow_path = Path('.github/workflows/release.yml')
    assert workflow_path.exists(), (
        'Expected release workflow at .github/workflows/release.yml for task 1.3'
    )
    with workflow_path.open('r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    assert isinstance(data, dict), 'Workflow YAML must be a mapping'
    return data


def _get_release_job_steps() -> list[dict]:
    workflow = _load_release_workflow()
    jobs = workflow.get('jobs')
    assert isinstance(jobs, dict), 'Workflow must define jobs'

    release_job = jobs.get('release')
    assert isinstance(release_job, dict), "Workflow must define 'release' job"

    steps = release_job.get('steps')
    assert isinstance(steps, list), "'release' job must define steps list"
    return steps


def _find_step(steps: list[dict], step_name: str) -> tuple[int, dict]:
    for index, step in enumerate(steps):
        if isinstance(step, dict) and step.get('name') == step_name:
            return index, step
    raise AssertionError(f"Missing required step '{step_name}' in release job")


def _load_package_binary_module():
    module_path = Path('scripts/release/package_binary.py')
    spec = importlib.util.spec_from_file_location('package_binary', module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_workflow_wires_version_into_package_step() -> None:
    steps = _get_release_job_steps()

    _, package_step = _find_step(steps, 'Package standalone binary')
    package_run = package_step.get('run')
    assert isinstance(package_run, str), 'Package step must define run command'

    assert '--version' in package_run, (
        'Package step must pass explicit --version to package script'
    )
    assert 'steps.resolve_release_version.outputs.release_version' in package_run, (
        'Package step must wire resolved release_version output into package command'
    )


def test_release_workflow_has_release_version_inventory_and_upload_steps() -> None:
    steps = _get_release_job_steps()

    package_index, _ = _find_step(steps, 'Package standalone binary')
    inventory_index, inventory_step = _find_step(
        steps, 'Verify packaged artifact naming inventory'
    )
    metadata_index, metadata_step = _find_step(steps, 'Capture packaged artifact metadata')
    workflow_upload_index, workflow_upload_step = _find_step(
        steps, 'Upload packaged workflow artifact'
    )
    release_upload_index, release_upload_step = _find_step(
        steps, 'Upload packaged GitHub Release asset'
    )

    assert package_index < inventory_index < metadata_index < workflow_upload_index < release_upload_index, (
        'Release workflow must run package -> inventory -> metadata -> workflow upload -> release upload'
    )

    inventory_run = inventory_step.get('run')
    assert isinstance(inventory_run, str), 'Inventory step must define run command'
    assert 'apidev-${{ steps.resolve_release_version.outputs.release_version }}-' in inventory_run, (
        'Inventory step must validate deterministic apidev-<version>-<os>-<arch> naming prefix'
    )

    metadata_id = metadata_step.get('id')
    assert metadata_id == 'package_metadata', (
        "Capture packaged artifact metadata step must use id 'package_metadata'"
    )

    workflow_uses = workflow_upload_step.get('uses')
    assert isinstance(workflow_uses, str), (
        'Workflow artifact upload step must use a GitHub Action'
    )
    assert re.fullmatch(
        r'actions/upload-artifact@[0-9a-f]{40}',
        workflow_uses,
    ), (
        'Workflow artifact upload step must pin actions/upload-artifact to a full commit SHA'
    )

    workflow_upload_with = workflow_upload_step.get('with')
    assert isinstance(workflow_upload_with, dict), (
        "Workflow artifact upload step must define 'with' mapping"
    )
    assert workflow_upload_with.get('name') == '${{ steps.package_metadata.outputs.archive_stem }}', (
        'Workflow artifact upload name must match deterministic archive stem'
    )
    assert workflow_upload_with.get('path') == '${{ steps.package_metadata.outputs.archive_path }}', (
        'Workflow artifact upload path must target packaged archive path'
    )

    release_if = release_upload_step.get('if')
    assert isinstance(release_if, str), 'Release upload step must define if condition'
    assert "github.event_name == 'release'" in release_if, (
        'Release upload step must be gated to release event'
    )
    assert "github.event.action == 'published'" in release_if, (
        "Release upload step must be gated to published release action"
    )


def test_release_workflow_release_upload_uses_gh_cli_with_release_tag() -> None:
    steps = _get_release_job_steps()

    _, release_upload_step = _find_step(steps, 'Upload packaged GitHub Release asset')

    upload_run = release_upload_step.get('run')
    assert isinstance(upload_run, str), 'Release upload step must define run command'
    assert 'gh release upload' in upload_run, (
        'Release upload step must use gh release upload command'
    )
    assert '${{ github.event.release.tag_name }}' in upload_run, (
        'Release upload must target published release tag'
    )
    assert '${{ steps.package_metadata.outputs.archive_path }}' in upload_run, (
        'Release upload must publish the packaged archive path from metadata step'
    )


def test_release_workflow_inventory_check_is_portable_without_mapfile() -> None:
    steps = _get_release_job_steps()

    _, inventory_step = _find_step(steps, 'Verify packaged artifact naming inventory')
    inventory_run = inventory_step.get('run')
    assert isinstance(inventory_run, str), 'Inventory step must define run command'

    assert 'mapfile' not in inventory_run, (
        'Inventory verification must avoid mapfile because it is not portable across runners'
    )
    assert 'while IFS= read -r archive_path' in inventory_run, (
        'Inventory verification must use POSIX-compatible read loop to collect archives'
    )
    assert 'archive_count=$((archive_count + 1))' in inventory_run, (
        'Inventory verification must keep strict exactly-one-archive counting logic'
    )


def test_package_binary_resolves_versioned_archive_name_for_required_targets() -> None:
    module = _load_package_binary_module()

    assert (
        module._resolve_archive_name('Linux', 'X64', None, '1.2.3')
        == 'apidev-1.2.3-linux-x64.tar.gz'
    )
    assert (
        module._resolve_archive_name('Windows', 'ARM64', None, '1.2.3')
        == 'apidev-1.2.3-windows-arm64.zip'
    )
    assert (
        module._resolve_archive_name('macOS', 'ARM64', None, '1.2.3')
        == 'apidev-1.2.3-macos-arm64.tar.gz'
    )


def test_package_binary_rejects_empty_version_for_deterministic_naming() -> None:
    module = _load_package_binary_module()

    try:
        module._resolve_archive_name('linux', 'x64', None, '')
        raise AssertionError('Expected ValueError for empty release version')
    except ValueError as error:
        assert 'version' in str(error).lower()
