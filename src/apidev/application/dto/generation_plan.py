from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

DriftStatus = Literal["drift", "no-drift", "error"]


@dataclass(slots=True)
class PlannedChange:
    path: Path
    content: str
    change_type: str


@dataclass(slots=True)
class GenerationPlan:
    generated_root: Path
    changes: list[PlannedChange] = field(default_factory=list)


@dataclass(slots=True)
class GenerateResult:
    applied_changes: int
    drift_status: DriftStatus = "no-drift"
    changed_paths: list[Path] = field(default_factory=list)

    @property
    def drift_detected(self) -> bool:
        return self.drift_status == "drift"
