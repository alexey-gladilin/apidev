from dataclasses import dataclass, field
import json
from typing import Mapping, Sequence

from apidev.core.constants import (
    DIAG_CODE_INIT_MODE_CONFLICT,
    DIAG_CODE_INIT_PROFILE_INVALID_ENUM,
    DIAG_CODE_PATH_BOUNDARY_VIOLATION,
)
from apidev.core.models.diagnostic import ValidationDiagnostic
from apidev.core.models.operation import Operation

Severity = str

FAIL_FAST_ERROR_CODES: tuple[str, ...] = (
    DIAG_CODE_PATH_BOUNDARY_VIOLATION,
    "validation.OUTPUT_CONTOUR_CONFLICT",
    "validation.INVALID_SCAFFOLD_WRITE_POLICY",
    "validation.MANUAL_TAGS_FORBIDDEN",
    "validation.RELEASE_STATE_INVALID_KEY",
    "validation.RELEASE_STATE_TYPE_MISMATCH",
    DIAG_CODE_INIT_PROFILE_INVALID_ENUM,
    DIAG_CODE_INIT_MODE_CONFLICT,
)


def canonicalize_context(context: Mapping[str, object] | None) -> dict[str, object]:
    if not context:
        return {}
    canonical: dict[str, object] = {}
    for key in sorted(str(item) for item in context.keys()):
        value = context.get(key)
        if value is None:
            continue
        canonical[key] = value
    return canonical


@dataclass(slots=True)
class ValidationResult:
    operations: list[Operation] = field(default_factory=list)
    diagnostics: list["ValidationDiagnostic"] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for diagnostic in self.diagnostics if diagnostic.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for diagnostic in self.diagnostics if diagnostic.severity == "warning")

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    def summary(self) -> dict[str, int | str]:
        return {
            "operations": len(self.operations),
            "errors": self.error_count,
            "warnings": self.warning_count,
            "status": "failed" if self.has_errors else "ok",
        }


def _severity_rank(severity: str) -> int:
    if severity == "error":
        return 0
    if severity == "warning":
        return 1
    return 2


def build_summary(
    diagnostics: Sequence[Mapping[str, object]],
    *,
    applied_changes: int | None = None,
) -> dict[str, int | str]:
    errors = sum(1 for item in diagnostics if item.get("severity") == "error")
    warnings = sum(1 for item in diagnostics if item.get("severity") == "warning")
    summary: dict[str, int | str] = {
        "status": "failed" if errors > 0 else "ok",
        "errors": errors,
        "warnings": warnings,
        "diagnostics_total": len(diagnostics),
    }
    if applied_changes is not None:
        summary["applied_changes"] = applied_changes
    return summary


def sort_diagnostics(diagnostics: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    def _context_sort_key(item: Mapping[str, object]) -> str:
        raw_context = item.get("context")
        if not isinstance(raw_context, Mapping):
            return ""
        return json.dumps(
            canonicalize_context(raw_context),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    ordered = sorted(
        diagnostics,
        key=lambda item: (
            _severity_rank(str(item.get("severity", "info"))),
            str(item.get("code", "")),
            str(item.get("location", "")),
            str(item.get("message", "")),
            str(item.get("detail", "")),
            _context_sort_key(item),
        ),
    )
    return [dict(item) for item in ordered]


def build_envelope(
    *,
    command: str,
    mode: str,
    diagnostics: Sequence[Mapping[str, object]],
    drift_status: str | None = None,
    compatibility: dict[str, object] | None = None,
    summary_extras: dict[str, object] | None = None,
    meta: dict[str, object] | None = None,
) -> dict[str, object]:
    ordered_diagnostics = sort_diagnostics(diagnostics)
    applied_changes = None
    if summary_extras:
        raw_applied_changes = summary_extras.get("applied_changes")
        if isinstance(raw_applied_changes, int):
            applied_changes = raw_applied_changes
    payload: dict[str, object] = {
        "command": command,
        "mode": mode,
        "summary": build_summary(ordered_diagnostics, applied_changes=applied_changes),
        "diagnostics": ordered_diagnostics,
    }
    if drift_status is not None:
        payload["drift_status"] = drift_status
    if compatibility is not None:
        payload["compatibility"] = compatibility
    if meta:
        payload["meta"] = meta
    return payload


def serialize_validation_diagnostic(
    diagnostic: ValidationDiagnostic,
    *,
    source: str = "validate-service",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "code": diagnostic.normalized_code(),
        "severity": diagnostic.severity,
        "location": diagnostic.location,
        "message": diagnostic.message,
        "category": "validation",
        "source": source,
        "rule": diagnostic.rule,
    }
    if diagnostic.context:
        payload["context"] = canonicalize_context(diagnostic.context)
    return payload
