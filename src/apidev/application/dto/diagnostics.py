from dataclasses import dataclass, field

from apidev.core.models.diagnostic import ValidationDiagnostic
from apidev.core.models.operation import Operation

Severity = str


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
    diagnostics: list[dict[str, object]],
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


def sort_diagnostics(diagnostics: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        diagnostics,
        key=lambda item: (
            _severity_rank(str(item.get("severity", "info"))),
            str(item.get("code", "")),
            str(item.get("location", "")),
            str(item.get("message", "")),
            str(item.get("detail", "")),
        ),
    )


def build_envelope(
    *,
    command: str,
    mode: str,
    diagnostics: list[dict[str, object]],
    drift_status: str | None = None,
    compatibility: dict[str, object] | None = None,
    summary_extras: dict[str, object] | None = None,
    meta: dict[str, object] | None = None,
) -> dict[str, object]:
    ordered_diagnostics = sort_diagnostics(diagnostics)
    applied_changes = None
    if summary_extras and isinstance(summary_extras.get("applied_changes"), int):
        applied_changes = int(summary_extras["applied_changes"])
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
) -> dict[str, str]:
    return {
        "code": diagnostic.normalized_code(),
        "severity": diagnostic.severity,
        "location": diagnostic.location,
        "message": diagnostic.message,
        "category": "validation",
        "source": source,
        "rule": diagnostic.rule,
    }
