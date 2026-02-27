from dataclasses import dataclass, field

from apidev.core.models.diagnostic import ValidationDiagnostic
from apidev.core.models.operation import Operation


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
