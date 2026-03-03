from __future__ import annotations

from pathlib import Path

import yaml


def _load_release_workflow() -> dict:
    workflow_path = Path(".github/workflows/release.yml")
    assert (
        workflow_path.exists()
    ), "Expected baseline release workflow at .github/workflows/release.yml"
    with workflow_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    assert isinstance(data, dict), "Workflow YAML must be a mapping"
    return data


def test_release_workflow_has_required_triggers() -> None:
    workflow = _load_release_workflow()

    on_block = workflow.get("on")
    assert isinstance(on_block, dict), "Workflow must define an 'on' mapping"

    release = on_block.get("release")
    assert isinstance(release, dict), "Workflow must define 'release' trigger options"
    assert release.get("types") == ["published"], "Release trigger must be limited to 'published'"

    assert (
        "workflow_dispatch" in on_block
    ), "Workflow must support manual trigger 'workflow_dispatch'"
    workflow_dispatch = on_block.get("workflow_dispatch")
    assert isinstance(
        workflow_dispatch, dict
    ), "Manual trigger 'workflow_dispatch' must be an explicit mapping"


def test_release_workflow_has_multi_os_matrix_targets() -> None:
    workflow = _load_release_workflow()

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs"
    assert "release" in jobs, "Workflow must define the baseline 'release' job"

    release_job = jobs["release"]
    strategy = release_job.get("strategy")
    assert isinstance(strategy, dict), "'release' job must define strategy"

    matrix = strategy.get("matrix")
    assert isinstance(matrix, dict), "'release' strategy must define matrix"
    os_values = matrix.get("os")

    assert os_values == [
        "ubuntu-latest",
        "macos-latest",
        "windows-latest",
    ], "Matrix must cover Linux/macOS/Windows in deterministic order"


def test_release_workflow_defines_minimal_permissions() -> None:
    workflow = _load_release_workflow()

    permissions = workflow.get("permissions")
    assert isinstance(permissions, dict), "Workflow must define explicit permissions mapping"
    assert permissions == {
        "contents": "read"
    }, "Workflow must set minimal top-level permissions to {'contents': 'read'}"


def test_release_workflow_pins_checkout_action_to_full_commit_sha() -> None:
    workflow = _load_release_workflow()

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs"

    release_job = jobs.get("release")
    assert isinstance(release_job, dict), "Workflow must define the baseline 'release' job"

    steps = release_job.get("steps")
    assert isinstance(steps, list), "'release' job must define steps"
    assert steps, "'release' job must include at least one step"

    checkout_step = steps[0]
    assert isinstance(checkout_step, dict), "Checkout step must be a mapping"

    uses = checkout_step.get("uses")
    assert isinstance(uses, str), "Checkout step must define 'uses' as a string"
    assert uses.startswith("actions/checkout@"), "Checkout step must use 'actions/checkout'"

    checkout_ref = uses.split("@", 1)[1]
    assert len(checkout_ref) == 40 and all(
        char in "0123456789abcdef" for char in checkout_ref
    ), "Checkout action must be pinned to an immutable full 40-char lowercase commit SHA"
