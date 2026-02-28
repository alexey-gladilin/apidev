from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class BaselineSnapshot:
    baseline_ref: str
    operations: dict[str, str]
    source: str
