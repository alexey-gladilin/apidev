from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_ROOT = REPO_ROOT / "docs"

STATUS_PATTERN = re.compile(r"^Статус:\s*`([^`]+)`\s*$", re.MULTILINE)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
WHITESPACE_PATTERN = re.compile(r"\s+")
NORMATIVE_MARKERS = (
    "должен",
    "должна",
    "должны",
    "обязател",
    "запрещ",
    "каноничес",
    "единственн",
    "норматив",
)
COMMAND_PATTERN = re.compile(r"`(apidev\s+[a-z-]+)`")
CANONICAL_LINE_PATTERN = re.compile(r"каноническ[а-я\s]+", re.IGNORECASE)
RELEASE_STEP_REF_PATTERN = re.compile(r"Step `([^`]+)`")
RELEASE_PROCESS_GATE_PATTERN = re.compile(r"^\d+\.\s+`([^`]+)`$", re.MULTILINE)


def _repo_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _authoritative_docs() -> list[Path]:
    docs: list[Path] = []
    for path in sorted(DOC_ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        status_match = STATUS_PATTERN.search(text)
        if status_match and status_match.group(1).strip() == "Authoritative":
            docs.append(path)
    return docs


def _normalize_sentence(text: str) -> str:
    lowered = text.lower().strip()
    lowered = lowered.replace("ё", "е")
    lowered = lowered.strip("-* ")
    lowered = WHITESPACE_PATTERN.sub(" ", lowered)
    return lowered


def _normative_sentences(text: str) -> set[str]:
    candidates = SENTENCE_SPLIT_PATTERN.split(text)
    normalized: set[str] = set()
    for candidate in candidates:
        sentence = _normalize_sentence(candidate)
        if len(sentence) < 80:
            continue
        if "```" in sentence or sentence.startswith("#"):
            continue
        if not any(marker in sentence for marker in NORMATIVE_MARKERS):
            continue
        normalized.add(sentence)
    return normalized


def test_no_duplicate_normative_statements_across_authoritative_docs() -> None:
    authoritative_docs = _authoritative_docs()
    sentence_to_docs: dict[str, set[str]] = {}

    for path in authoritative_docs:
        text = path.read_text(encoding="utf-8")
        for sentence in _normative_sentences(text):
            sentence_to_docs.setdefault(sentence, set()).add(_repo_rel(path))

    offenders = [
        f"{sorted(paths)} -> {sentence[:140]}..."
        for sentence, paths in sentence_to_docs.items()
        if len(paths) > 1
    ]
    assert offenders == []


def test_canonical_generate_command_is_consistent_in_authoritative_docs() -> None:
    authoritative_docs = _authoritative_docs()
    canonical_claims: list[tuple[str, str]] = []

    for path in authoritative_docs:
        rel = _repo_rel(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not CANONICAL_LINE_PATTERN.search(line):
                continue

            search_window = [line]
            if index + 1 < len(lines):
                search_window.append(lines[index + 1])
            joined = " ".join(search_window)
            for command in COMMAND_PATTERN.findall(joined):
                if command.startswith("apidev gen") or command.startswith("apidev generate"):
                    canonical_claims.append((rel, command))

    canonical_mentions = [item for item in canonical_claims if item[1] == "apidev gen"]
    non_canonical_mentions = [item for item in canonical_claims if item[1] != "apidev gen"]

    assert canonical_mentions, "No canonical `apidev gen` mention found in authoritative docs."
    assert non_canonical_mentions == []


def test_release_checklist_quality_gates_reference_existing_release_workflow_steps() -> None:
    workflow_path = REPO_ROOT / ".github" / "workflows" / "release.yml"
    checklist_path = REPO_ROOT / "docs" / "process" / "release-checklist.md"
    assert workflow_path.exists(), "Missing .github/workflows/release.yml"
    assert checklist_path.exists(), "Missing docs/process/release-checklist.md"

    workflow_text = workflow_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")

    referenced_steps = RELEASE_STEP_REF_PATTERN.findall(checklist_text)
    assert referenced_steps, "release-checklist must reference workflow quality gate steps"

    missing = [step for step in referenced_steps if f"- name: {step}" not in workflow_text]
    assert missing == []


def test_release_quality_gate_lists_stay_synced_between_process_and_checklist_docs() -> None:
    process_path = REPO_ROOT / "docs" / "process" / "release-process.md"
    checklist_path = REPO_ROOT / "docs" / "process" / "release-checklist.md"
    assert process_path.exists(), "Missing docs/process/release-process.md"
    assert checklist_path.exists(), "Missing docs/process/release-checklist.md"

    process_text = process_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")

    process_steps = RELEASE_PROCESS_GATE_PATTERN.findall(process_text)
    checklist_steps = RELEASE_STEP_REF_PATTERN.findall(checklist_text)

    assert process_steps, "release-process must list workflow quality gate steps"
    assert checklist_steps, "release-checklist must list workflow quality gate steps"
    assert process_steps == [
        step for step in checklist_steps if step != "Pre-check workflow_dispatch version input"
    ]
