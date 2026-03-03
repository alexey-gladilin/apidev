from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
RELEASE_PROCESS_PATH = REPO_ROOT / "docs" / "process" / "release-process.md"
RELEASE_CHECKLIST_PATH = REPO_ROOT / "docs" / "process" / "release-checklist.md"

EXPECTED_CHECKLIST_GATE_STEPS = [
    "Pre-check workflow_dispatch version input",
    "Build standalone binary",
    "Smoke check standalone binary",
    "Resolve release version",
    "Package standalone binary",
    "Verify packaged artifact naming inventory",
    "Upload packaged workflow artifact",
    "Upload packaged GitHub Release asset",
]

EXPECTED_PROCESS_GATE_STEPS = [
    "Build standalone binary",
    "Smoke check standalone binary",
    "Resolve release version",
    "Package standalone binary",
    "Verify packaged artifact naming inventory",
    "Upload packaged workflow artifact",
    "Upload packaged GitHub Release asset",
]

CHECKLIST_STEP_REF_PATTERN = re.compile(r"Step `([^`]+)`")
PROCESS_GATE_LINE_PATTERN = re.compile(r"^\d+\.\s+`([^`]+)`$", re.MULTILINE)


def _load_release_workflow() -> dict:
    assert (
        RELEASE_WORKFLOW_PATH.exists()
    ), "Expected release workflow at .github/workflows/release.yml for task 3.1"
    with RELEASE_WORKFLOW_PATH.open("r", encoding="utf-8") as file:
        workflow = yaml.safe_load(file)
    assert isinstance(workflow, dict), "Workflow YAML must be a mapping"
    return workflow


def _release_step_names(workflow: dict) -> list[str]:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"
    release_job = jobs.get("release")
    assert isinstance(release_job, dict), "Workflow must define 'release' job"
    steps = release_job.get("steps")
    assert isinstance(steps, list) and steps, "'release' job must define non-empty steps"

    names: list[str] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        step_name = step.get("name")
        if isinstance(step_name, str) and step_name.strip():
            names.append(step_name)
    return names


def _extract_checklist_gate_steps() -> list[str]:
    assert RELEASE_CHECKLIST_PATH.exists(), "Expected docs/process/release-checklist.md to exist"
    content = RELEASE_CHECKLIST_PATH.read_text(encoding="utf-8")
    return CHECKLIST_STEP_REF_PATTERN.findall(content)


def _extract_process_gate_steps() -> list[str]:
    assert RELEASE_PROCESS_PATH.exists(), "Expected docs/process/release-process.md to exist"
    content = RELEASE_PROCESS_PATH.read_text(encoding="utf-8")
    return PROCESS_GATE_LINE_PATTERN.findall(content)


def test_release_checklist_quality_gate_step_references_are_explicit_and_stable() -> None:
    checklist_steps = _extract_checklist_gate_steps()
    assert (
        checklist_steps == EXPECTED_CHECKLIST_GATE_STEPS
    ), "release-checklist quality gate step references changed; update tests and docs explicitly"


def test_release_docs_quality_gates_reference_existing_release_workflow_steps() -> None:
    workflow = _load_release_workflow()
    workflow_step_names = set(_release_step_names(workflow))
    checklist_steps = _extract_checklist_gate_steps()

    missing = [step for step in checklist_steps if step not in workflow_step_names]
    assert missing == [], "release-checklist references unknown workflow steps: " + ", ".join(
        sorted(missing)
    )


def test_release_process_quality_gate_list_matches_checklist_contract() -> None:
    process_steps = _extract_process_gate_steps()
    checklist_steps = _extract_checklist_gate_steps()

    assert (
        process_steps == EXPECTED_PROCESS_GATE_STEPS
    ), "release-process quality gate list changed; update tests and docs explicitly"
    assert process_steps == [
        step for step in checklist_steps if step != "Pre-check workflow_dispatch version input"
    ], "release-process and release-checklist quality gate lists are out of sync"
