from __future__ import annotations

from pathlib import Path

import yaml


def _load_release_workflow() -> dict:
    workflow_path = Path(".github/workflows/release.yml")
    assert (
        workflow_path.exists()
    ), "Expected release workflow at .github/workflows/release.yml for task 2.3"
    with workflow_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    assert isinstance(data, dict), "Workflow YAML must be a mapping"
    return data


def _get_job(workflow: dict, job_id: str) -> dict:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"

    job = jobs.get(job_id)
    assert isinstance(job, dict), f"Workflow must define '{job_id}' job"
    return job


def _find_step(steps: list[dict], step_name: str) -> dict:
    for step in steps:
        if isinstance(step, dict) and step.get("name") == step_name:
            return step
    raise AssertionError(f"Missing required step '{step_name}'")


def test_release_workflow_defines_isolated_homebrew_publish_job() -> None:
    workflow = _load_release_workflow()
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"

    release_job = _get_job(workflow, "release")
    homebrew_job = _get_job(workflow, "publish-homebrew")

    assert (
        homebrew_job.get("needs") == "release"
    ), "Homebrew publish path must depend on core release job completion"
    assert (
        "needs" not in release_job or release_job.get("needs") != "publish-homebrew"
    ), "Core release job chain must not depend on Homebrew path"

    for job_id, job_body in jobs.items():
        if job_id in {"release", "publish-homebrew"} or not isinstance(job_body, dict):
            continue
        assert (
            job_body.get("needs") != "publish-homebrew"
        ), "Homebrew path must be isolated and not block unrelated jobs"


def test_homebrew_precheck_enforces_secret_presence_and_basic_validity() -> None:
    workflow = _load_release_workflow()
    homebrew_job = _get_job(workflow, "publish-homebrew")

    steps = homebrew_job.get("steps")
    assert isinstance(steps, list) and steps, "Homebrew job must define steps"

    precheck_step = _find_step(steps, "Pre-check Homebrew tap token secret")
    assert (
        precheck_step.get("id") == "precheck_homebrew_secret"
    ), "Homebrew pre-check step must expose id 'precheck_homebrew_secret'"

    env = precheck_step.get("env")
    assert isinstance(env, dict), "Homebrew pre-check must define env mapping"
    assert (
        env.get("HOMEBREW_TAP_TOKEN") == "${{ secrets.HOMEBREW_TAP_TOKEN }}"
    ), "Homebrew pre-check must read HOMEBREW_TAP_TOKEN from secrets context"

    run = precheck_step.get("run")
    assert isinstance(run, str), "Homebrew pre-check must define run command"
    assert (
        "Missing required secret HOMEBREW_TAP_TOKEN" in run
    ), "Homebrew pre-check must fail with controlled message when secret is missing"
    assert (
        "HOMEBREW_TAP_TOKEN has unsupported format" in run
    ), "Homebrew pre-check must fail with controlled message when secret format is invalid"
    assert (
        "github_pat_*" in run
    ), "Homebrew pre-check must explicitly allow fine-grained PAT format only"
    assert (
        "ghp_*" not in run
    ), "Homebrew pre-check must not allow classic PAT format to prevent over-privileged tokens"
    assert "exit 1" in run, "Homebrew pre-check must hard fail on missing/invalid secret"


def test_publish_homebrew_job_permissions_are_locked_to_contents_read() -> None:
    workflow = _load_release_workflow()
    homebrew_job = _get_job(workflow, "publish-homebrew")

    permissions = homebrew_job.get("permissions")
    assert isinstance(permissions, dict), "publish-homebrew job must define explicit permissions"
    assert permissions == {
        "contents": "read"
    }, "publish-homebrew permissions must stay locked to contents: read"


def test_homebrew_publish_positive_path_is_explicitly_gated_by_precheck_output() -> None:
    workflow = _load_release_workflow()
    homebrew_job = _get_job(workflow, "publish-homebrew")

    steps = homebrew_job.get("steps")
    assert isinstance(steps, list) and steps, "Homebrew job must define steps"

    precheck_step = _find_step(steps, "Pre-check Homebrew tap token secret")
    precheck_run = precheck_step.get("run")
    assert isinstance(precheck_run, str), "Homebrew pre-check must define run command"
    assert (
        'echo "ready=true" >> "$GITHUB_OUTPUT"' in precheck_run
    ), "Homebrew pre-check must emit ready=true output for positive path"

    publish_step = _find_step(steps, "Publish Homebrew formula placeholder")
    publish_if = publish_step.get("if")
    assert (
        publish_if == "${{ steps.precheck_homebrew_secret.outputs.ready == 'true' }}"
    ), "Homebrew publish step must run only after successful secret pre-check"


def test_core_release_upload_step_remains_independent_from_homebrew_failures() -> None:
    workflow = _load_release_workflow()
    release_job = _get_job(workflow, "release")

    steps = release_job.get("steps")
    assert isinstance(steps, list) and steps, "Release job must define steps"

    upload_release_step = _find_step(steps, "Upload packaged GitHub Release asset")
    upload_if = upload_release_step.get("if")
    assert isinstance(upload_if, str), "Release asset upload step must define if condition"
    assert (
        "precheck_homebrew_secret" not in upload_if
    ), "Core release asset upload must not be gated by Homebrew secret pre-check"
