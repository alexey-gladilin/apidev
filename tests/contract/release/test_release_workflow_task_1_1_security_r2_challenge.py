from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _load_release_workflow() -> dict:
    workflow_path = Path(".github/workflows/release.yml")
    assert workflow_path.exists(), "Expected release workflow at .github/workflows/release.yml"
    with workflow_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    assert isinstance(data, dict), "Workflow YAML must be a mapping"
    return data


def _write_release_workflow(tmp_path: Path, workflow_data: dict) -> None:
    workflow_path = tmp_path / ".github" / "workflows" / "release.yml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(yaml.safe_dump(workflow_data, sort_keys=False), encoding="utf-8")


def _publish_homebrew_steps(workflow: dict) -> list[dict]:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"

    job = jobs.get("publish-homebrew")
    assert isinstance(job, dict), "Workflow must define 'publish-homebrew' job"

    steps = job.get("steps")
    assert isinstance(steps, list) and steps, "publish-homebrew job must define non-empty steps"
    return steps


def _find_step(steps: list[dict], name: str) -> dict:
    for step in steps:
        if isinstance(step, dict) and step.get("name") == name:
            return step
    raise AssertionError(f"Missing required step '{name}'")


def _assert_checkout_persist_credentials_false(workflow: dict) -> None:
    steps = _publish_homebrew_steps(workflow)

    source_checkout = _find_step(steps, "Checkout source repository")
    source_with = source_checkout.get("with")
    assert isinstance(source_with, dict), "Source checkout step must define with mapping"
    assert (
        source_with.get("persist-credentials") is False
    ), "Source checkout must set persist-credentials: false"

    tap_checkout = _find_step(steps, "Checkout Homebrew tap repository")
    tap_with = tap_checkout.get("with")
    assert isinstance(tap_with, dict), "Tap checkout step must define with mapping"
    assert (
        tap_with.get("persist-credentials") is False
    ), "Tap checkout must set persist-credentials: false"


def test_publish_homebrew_checkout_steps_disable_credential_persistence() -> None:
    workflow = _load_release_workflow()
    _assert_checkout_persist_credentials_false(workflow)


def test_publish_homebrew_source_checkout_rejects_missing_persist_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_release_workflow(
        tmp_path,
        {
            "name": "Release",
            "on": {"release": {"types": ["published"]}},
            "jobs": {
                "publish-homebrew": {
                    "steps": [
                        {
                            "name": "Checkout source repository",
                            "uses": "actions/checkout@sha",
                            "with": {},
                        },
                        {
                            "name": "Checkout Homebrew tap repository",
                            "uses": "actions/checkout@sha",
                            "with": {"persist-credentials": False},
                        },
                    ]
                }
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(AssertionError, match="Source checkout must set persist-credentials: false"):
        _assert_checkout_persist_credentials_false(_load_release_workflow())


def test_publish_homebrew_tap_checkout_rejects_non_false_persist_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_release_workflow(
        tmp_path,
        {
            "name": "Release",
            "on": {"release": {"types": ["published"]}},
            "jobs": {
                "publish-homebrew": {
                    "steps": [
                        {
                            "name": "Checkout source repository",
                            "uses": "actions/checkout@sha",
                            "with": {"persist-credentials": False},
                        },
                        {
                            "name": "Checkout Homebrew tap repository",
                            "uses": "actions/checkout@sha",
                            "with": {"persist-credentials": True},
                        },
                    ]
                }
            },
        },
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(AssertionError, match="Tap checkout must set persist-credentials: false"):
        _assert_checkout_persist_credentials_false(_load_release_workflow())
