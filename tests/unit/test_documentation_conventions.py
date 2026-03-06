from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DOC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "CONTRIBUTING.md",
    *sorted((REPO_ROOT / "docs").rglob("*.md")),
    REPO_ROOT / "openspec" / "project.md",
]

LEGACY_DOC_PATHS = {
    "docs/architecture.md",
    "docs/ai-workflow-guide.md",
    "docs/cli-conventions.md",
    "docs/apidev-concept-and-approach.md",
    "docs/prompt-improvement-regression-cases.md",
}

CANONICAL_DOC_PATHS = {
    "docs/README.md",
    "docs/product/vision.md",
    "docs/architecture/architecture-overview.md",
    "docs/architecture/architecture-rules.md",
    "docs/process/testing-strategy.md",
    "docs/process/ai-workflow.md",
    "docs/process/prompt-improvement-regression-cases.md",
    "docs/reference/cli-contract.md",
    "docs/reference/contract-format.md",
    "docs/reference/glossary.md",
    "docs/decisions/README.md",
    "CONTRIBUTING.md",
}

GENERATE_ALIAS_ALLOWED = {
    "README.md",
    "docs/reference/cli-contract.md",
    "openspec/project.md",
}

DOC_PATH_PATTERN = re.compile(
    r"(?:^|[`( ])((?:docs|openspec)/[A-Za-z0-9_./-]+\.md|CONTRIBUTING\.md)(?:[` )]|$)"
)
CONTRACT_FORMAT_DOC_PATH = REPO_ROOT / "docs" / "reference" / "contract-format.md"
CANONICAL_CONFIG_KEYS = (
    "paths.templates_dir",
    "inputs.contracts_dir",
    "inputs.shared_models_dir",
    "generator.generated_dir",
    "generator.postprocess",
    "generator.scaffold",
    "generator.scaffold_dir",
    "generator.scaffold_write_policy",
    "evolution.release_state_file",
    "evolution.compatibility_policy",
    "evolution.grace_period_releases",
    "openapi.include_extensions",
)
LEGACY_CONFIG_KEYS = ("contracts.dir", "templates.dir", "paths.release_state_file")


def _repo_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_foundational_docs_exist() -> None:
    missing = [path for path in CANONICAL_DOC_PATHS if not (REPO_ROOT / path).exists()]
    assert missing == []


def test_docs_do_not_reference_removed_doc_paths() -> None:
    offenders: list[str] = []

    for path in DOC_FILES:
        text = path.read_text(encoding="utf-8")
        for legacy_path in LEGACY_DOC_PATHS:
            if legacy_path in text:
                offenders.append(f"{_repo_rel(path)} -> {legacy_path}")

    assert offenders == []


def test_only_allowed_docs_reference_generate_alias() -> None:
    offenders: list[str] = []

    for path in DOC_FILES:
        text = path.read_text(encoding="utf-8")
        if "apidev generate" not in text:
            continue
        rel = _repo_rel(path)
        if rel not in GENERATE_ALIAS_ALLOWED:
            offenders.append(rel)

    assert offenders == []


def test_all_referenced_markdown_docs_exist() -> None:
    missing_refs: list[str] = []

    for path in DOC_FILES:
        text = path.read_text(encoding="utf-8")
        refs = {match.group(1) for match in DOC_PATH_PATTERN.finditer(text)}
        for ref in sorted(refs):
            if not (REPO_ROOT / ref).exists():
                missing_refs.append(f"{_repo_rel(path)} -> {ref}")

    assert missing_refs == []


def test_contract_format_doc_uses_canonical_config_keys_only() -> None:
    text = CONTRACT_FORMAT_DOC_PATH.read_text(encoding="utf-8")
    for key in CANONICAL_CONFIG_KEYS:
        assert key in text
    for legacy_key in LEGACY_CONFIG_KEYS:
        assert legacy_key not in text
