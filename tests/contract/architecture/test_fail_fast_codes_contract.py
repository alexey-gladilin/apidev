"""AR-011: fail-fast error code catalog must stay contract-stable."""

from __future__ import annotations

from pathlib import Path

from apidev.application.dto.diagnostics import FAIL_FAST_ERROR_CODES


def _extract_codes_from_cli_contract(doc_text: str) -> tuple[str, ...]:
    start_marker = "### Нормативный каталог fail-fast error codes"
    end_marker = "### Summary schema"
    start = doc_text.index(start_marker)
    end = doc_text.index(end_marker, start)
    section = doc_text[start:end]

    codes: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- `") or not stripped.endswith("`"):
            continue
        codes.append(stripped[3:-1])
    return tuple(codes)


def test_fail_fast_catalog_matches_documented_contract() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    cli_contract = (repo_root / "docs" / "reference" / "cli-contract.md").read_text(
        encoding="utf-8"
    )

    documented_codes = _extract_codes_from_cli_contract(cli_contract)

    assert documented_codes == FAIL_FAST_ERROR_CODES
