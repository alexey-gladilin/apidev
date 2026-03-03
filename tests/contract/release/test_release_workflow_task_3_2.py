from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
RELEASE_PROCESS_PATH = REPO_ROOT / "docs" / "process" / "release-process.md"
RELEASE_CHECKLIST_PATH = REPO_ROOT / "docs" / "process" / "release-checklist.md"

PINNED_ACTION_REF_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

REQUIRED_CHECKLIST_LINES = [
    "- [ ] Все `uses:` в `.github/workflows/release.yml` pinned на immutable `@<40-hex-sha>` (без `@v*`, `@main`, `@master`).",
    "- [ ] В workflow задан top-level `permissions`, и у всех release jobs (`release`, `publish-homebrew`) заданы explicit `permissions`.",
    "- [ ] `release` job ограничен минимально необходимым доступом для публикации assets (`contents: write`), без дополнительных scopes.",
    "- [ ] `actions/checkout` запускается с `persist-credentials: false` и не оставляет токен в git-config шагов после checkout.",
    "- [ ] Release build использует детерминированные зависимости (`requirements/code.txt` + pinned tooling, включая `pyinstaller==...`).",
    "- [ ] Изменения в security/reproducibility guardrails подтверждены контрактными тестами release workflow.",
]

REQUIRED_PROCESS_GUARDRAILS = [
    "Все GitHub Actions в `.github/workflows/release.yml` должны быть pinned на immutable full-length commit SHA",
    "Для workflow и каждой release-job должны быть явные `permissions`",
    "actions/checkout` должен работать без сохранения credentials (`persist-credentials: false`",
    "Зависимости release-сборки должны быть детерминированы: lock-файл (`requirements/code.txt`)",
]


def _load_release_workflow() -> dict:
    assert (
        RELEASE_WORKFLOW_PATH.exists()
    ), "Expected release workflow at .github/workflows/release.yml for task 3.2"
    with RELEASE_WORKFLOW_PATH.open("r", encoding="utf-8") as file:
        workflow = yaml.safe_load(file)
    assert isinstance(workflow, dict), "Workflow YAML must be a mapping"
    return workflow


def _release_steps(workflow: dict) -> list[dict]:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"
    release_job = jobs.get("release")
    assert isinstance(release_job, dict), "Workflow must define 'release' job"
    steps = release_job.get("steps")
    assert isinstance(steps, list), "'release' job must define steps"
    return [step for step in steps if isinstance(step, dict)]


def _find_step(steps: list[dict], step_name: str) -> dict:
    for step in steps:
        if step.get("name") == step_name:
            return step
    raise AssertionError(f"Missing required release step '{step_name}'")


def _iter_uses_references(workflow: dict) -> list[str]:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"
    refs: list[str] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str):
                refs.append(uses)
    return refs


def test_release_workflow_all_actions_are_pinned_to_immutable_commit_sha() -> None:
    workflow = _load_release_workflow()
    uses_refs = _iter_uses_references(workflow)
    assert uses_refs, "Release workflow must use at least one pinned action"

    non_pinned = [ref for ref in uses_refs if not PINNED_ACTION_REF_PATTERN.fullmatch(ref)]
    assert non_pinned == [], (
        "All action references in release workflow must be pinned to full commit SHAs: "
        + ", ".join(sorted(non_pinned))
    )


def test_release_workflow_has_explicit_least_privilege_permissions_contract() -> None:
    workflow = _load_release_workflow()

    top_permissions = workflow.get("permissions")
    assert top_permissions == {
        "contents": "read"
    }, "Workflow must keep explicit top-level least-privilege permissions {'contents': 'read'}"

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Workflow must define jobs mapping"

    release_job = jobs.get("release")
    assert isinstance(release_job, dict), "Workflow must define 'release' job"
    assert release_job.get("permissions") == {
        "contents": "write"
    }, "Release job must keep minimal publish scope permissions {'contents': 'write'}"

    publish_homebrew_job = jobs.get("publish-homebrew")
    assert isinstance(publish_homebrew_job, dict), "Workflow must define 'publish-homebrew' job"
    assert publish_homebrew_job.get("permissions") == {
        "contents": "read"
    }, "publish-homebrew job must keep explicit least-privilege permissions {'contents': 'read'}"


def test_release_workflow_hardens_checkout_and_release_dependency_pinning() -> None:
    workflow = _load_release_workflow()
    steps = _release_steps(workflow)

    checkout_step = _find_step(steps, "Checkout")
    checkout_with = checkout_step.get("with")
    assert isinstance(checkout_with, dict), "Checkout step must define with mapping"
    assert (
        checkout_with.get("persist-credentials") is False
    ), "Checkout step must disable credential persistence for least-privilege hardening"
    assert (
        checkout_with.get("fetch-depth") == 1
    ), "Checkout step must use deterministic shallow clone depth 1"

    install_step = _find_step(steps, "Install release build dependencies")
    install_run = install_step.get("run")
    assert isinstance(
        install_run, str
    ), "Install release build dependencies must define run command"
    assert (
        "-r requirements/code.txt" in install_run
    ), "Release dependency installation must rely on pinned requirements/code.txt lock file"
    assert (
        "pyinstaller==6.18.0" in install_run
    ), "Release dependency installation must pin PyInstaller version"


def test_release_docs_include_security_reproducibility_review_checklist() -> None:
    assert (
        RELEASE_CHECKLIST_PATH.exists()
    ), "Expected docs/process/release-checklist.md for task 3.2 docs contract"
    checklist_content = RELEASE_CHECKLIST_PATH.read_text(encoding="utf-8")

    assert (
        "## Security/Reproducibility Review Checklist (обязательно)" in checklist_content
    ), "Release checklist must include explicit Security/Reproducibility Review section"
    for line in REQUIRED_CHECKLIST_LINES:
        assert (
            line in checklist_content
        ), "Release checklist must keep explicit security/reproducibility checklist items"


def test_release_process_documents_security_reproducibility_guardrails() -> None:
    assert (
        RELEASE_PROCESS_PATH.exists()
    ), "Expected docs/process/release-process.md for task 3.2 process contract"
    process_content = RELEASE_PROCESS_PATH.read_text(encoding="utf-8")

    assert (
        "## Security/Reproducibility Guardrails (обязательно)" in process_content
    ), "Release process must include explicit security/reproducibility guardrails section"
    for guardrail in REQUIRED_PROCESS_GUARDRAILS:
        assert (
            guardrail in process_content
        ), "Release process must document mandatory security/reproducibility guardrails"
