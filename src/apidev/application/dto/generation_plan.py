from dataclasses import dataclass, field
from pathlib import Path


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
    drift_detected: bool = False
