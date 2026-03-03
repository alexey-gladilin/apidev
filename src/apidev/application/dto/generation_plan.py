from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

DriftStatus = Literal["drift", "no-drift", "error"]
CompatibilityPolicy = Literal["warn", "strict"]
ChangeType = Literal["ADD", "UPDATE", "REMOVE", "SAME"]


@dataclass(slots=True, frozen=True)
class CompatibilityDiagnostic:
    category: str
    code: str
    location: str
    detail: str = ""

    def as_unified_dict(self) -> dict[str, object]:
        category = "compatibility"
        severity = "info"
        normalized_category = self.category.strip().lower()
        if normalized_category == "breaking":
            severity = "error"
        elif normalized_category == "potentially-breaking":
            severity = "warning"
        message = f"Compatibility diagnostic: {self.code}"
        payload: dict[str, object] = {
            "code": self.code,
            "severity": severity,
            "location": self.location,
            "message": message,
            "category": category,
            "source": "diff-service",
        }
        if self.detail:
            payload["detail"] = self.detail
        return payload


@dataclass(slots=True, frozen=True)
class GenerationDiagnostic:
    code: str
    location: str
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "detail": self.detail,
        }

    def as_unified_dict(self, *, source: str = "generate-service") -> dict[str, object]:
        category = "generation"
        if self.code.startswith("config."):
            category = "config"
        elif self.code.startswith("runtime."):
            category = "runtime"
        message = f"Generation diagnostic: {self.code}"
        payload: dict[str, object] = {
            "code": self.code,
            "severity": "error",
            "location": self.location,
            "message": message,
            "category": category,
            "source": source,
        }
        if self.detail:
            payload["detail"] = self.detail
        return payload


@dataclass(slots=True)
class CompatibilitySummary:
    overall: str = "non-breaking"
    counts: dict[str, int] = field(
        default_factory=lambda: {
            "non-breaking": 0,
            "potentially-breaking": 0,
            "breaking": 0,
        }
    )
    diagnostics: list[CompatibilityDiagnostic] = field(default_factory=list)


@dataclass(slots=True)
class PlannedChange:
    path: Path
    content: str
    change_type: ChangeType


@dataclass(slots=True)
class GenerationPlan:
    generated_root: Path
    changes: list[PlannedChange] = field(default_factory=list)
    compatibility_policy: CompatibilityPolicy = "warn"
    compatibility: CompatibilitySummary = field(default_factory=CompatibilitySummary)
    policy_blocked: bool = False


@dataclass(slots=True)
class GenerateResult:
    applied_changes: int
    drift_status: DriftStatus = "no-drift"
    changed_paths: list[Path] = field(default_factory=list)
    diagnostics: list[GenerationDiagnostic] = field(default_factory=list)
    compatibility_policy: CompatibilityPolicy = "warn"
    compatibility: CompatibilitySummary = field(default_factory=CompatibilitySummary)
    policy_blocked: bool = False

    @property
    def drift_detected(self) -> bool:
        return self.drift_status == "drift"
