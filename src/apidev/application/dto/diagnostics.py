from dataclasses import dataclass, field

from apidev.core.models.operation import Operation


@dataclass(slots=True)
class ValidationResult:
    operations: list[Operation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
