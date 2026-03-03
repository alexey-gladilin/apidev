from __future__ import annotations

from pathlib import Path

import yaml


def _load_release_workflow() -> dict:
    workflow_path = Path(".github/workflows/release.yml")
    assert (
        workflow_path.exists()
    ), "Expected release workflow at .github/workflows/release.yml for task 2.4"
    with workflow_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    assert isinstance(data, dict), "Workflow YAML must be a mapping"
    return data


def _get_release_job_steps(workflow: dict) -> list[dict]:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"
    release_job = jobs.get("release")
    assert isinstance(release_job, dict), "Workflow must define 'release' job"
    steps = release_job.get("steps")
    assert isinstance(steps, list) and steps, "'release' job must define non-empty steps"
    return steps


def _find_step(steps: list[dict], step_name: str) -> tuple[int, dict]:
    for index, step in enumerate(steps):
        if isinstance(step, dict) and step.get("name") == step_name:
            return index, step
    raise AssertionError(f"Missing required step '{step_name}'")


def test_workflow_dispatch_requires_explicit_release_version_input() -> None:
    workflow = _load_release_workflow()
    on_block = workflow.get("on")
    assert isinstance(on_block, dict), "Workflow must define an 'on' mapping"

    workflow_dispatch = on_block.get("workflow_dispatch")
    assert isinstance(
        workflow_dispatch, dict
    ), "workflow_dispatch trigger must remain an explicit mapping"
    inputs = workflow_dispatch.get("inputs")
    assert isinstance(inputs, dict), "workflow_dispatch must define inputs mapping"

    release_version_input = inputs.get("release_version")
    assert isinstance(
        release_version_input, dict
    ), "workflow_dispatch must define release_version input contract"
    assert (
        release_version_input.get("required") is True
    ), "workflow_dispatch release_version input must be mandatory"
    assert (
        release_version_input.get("type") == "string"
    ), "workflow_dispatch release_version input must use string type"


def test_workflow_dispatch_precheck_fails_fast_on_missing_or_empty_release_version() -> None:
    workflow = _load_release_workflow()
    steps = _get_release_job_steps(workflow)

    precheck_index, precheck_step = _find_step(steps, "Pre-check workflow_dispatch version input")
    build_index, _ = _find_step(steps, "Build standalone binary")
    package_index, _ = _find_step(steps, "Package standalone binary")

    assert (
        precheck_index < build_index < package_index
    ), "workflow_dispatch pre-check must run before build/package steps"

    precheck_if = precheck_step.get("if")
    assert (
        precheck_if == "${{ github.event_name == 'workflow_dispatch' }}"
    ), "workflow_dispatch pre-check must only run for manual trigger"

    precheck_run = precheck_step.get("run")
    assert isinstance(precheck_run, str), "workflow_dispatch pre-check must define run command"
    assert (
        "github.event.inputs.release_version" in precheck_run
    ), "workflow_dispatch pre-check must read release_version input"
    assert (
        "workflow_dispatch requires non-empty input release_version" in precheck_run
    ), "workflow_dispatch pre-check must fail with controlled message for empty input"
    assert "exit 1" in precheck_run, "workflow_dispatch pre-check must hard fail for empty input"


def test_release_version_resolution_contract_is_event_specific_without_ref_fallback() -> None:
    workflow = _load_release_workflow()
    steps = _get_release_job_steps(workflow)
    _, resolve_step = _find_step(steps, "Resolve release version")

    resolve_run = resolve_step.get("run")
    assert isinstance(resolve_run, str), "Resolve release version step must define run command"
    assert (
        'case "${{ github.event_name }}" in' in resolve_run
    ), "Release version resolution must branch by event source explicitly"
    assert (
        'raw_version="${{ github.event.release.tag_name }}"' in resolve_run
    ), "Release event must resolve version from release tag"
    assert (
        'raw_version="${{ github.event.inputs.release_version }}"' in resolve_run
    ), "workflow_dispatch must resolve version from release_version input"
    assert (
        "github.ref_name" not in resolve_run
    ), "Release version resolution must not fallback to github.ref_name"


def test_manual_runs_keep_deterministic_naming_bound_to_resolved_release_version() -> None:
    workflow = _load_release_workflow()
    steps = _get_release_job_steps(workflow)

    _, package_step = _find_step(steps, "Package standalone binary")
    _, inventory_step = _find_step(steps, "Verify packaged artifact naming inventory")

    package_run = package_step.get("run")
    inventory_run = inventory_step.get("run")
    assert isinstance(package_run, str), "Package step must define run command"
    assert isinstance(inventory_run, str), "Inventory step must define run command"

    assert (
        "steps.resolve_release_version.outputs.release_version" in package_run
    ), "Package step must keep deterministic version binding through resolve_release_version output"
    assert (
        "apidev-${{ steps.resolve_release_version.outputs.release_version }}-" in inventory_run
    ), "Inventory check must keep deterministic naming contract for manual runs"
