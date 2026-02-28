from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping


class CompatibilityCategory(str, Enum):
    NON_BREAKING = "non-breaking"
    POTENTIALLY_BREAKING = "potentially-breaking"
    BREAKING = "breaking"


# Default taxonomy can be extended by application layer when needed.
_DEFAULT_COMPATIBILITY_TAXONOMY: dict[str, CompatibilityCategory] = {
    "operation-added": CompatibilityCategory.NON_BREAKING,
    "response-optional-field-added": CompatibilityCategory.NON_BREAKING,
    "response-enum-expanded": CompatibilityCategory.NON_BREAKING,
    "deprecated-marked": CompatibilityCategory.NON_BREAKING,
    "request-optional-field-added": CompatibilityCategory.POTENTIALLY_BREAKING,
    "request-enum-expanded": CompatibilityCategory.POTENTIALLY_BREAKING,
    "auth-changed": CompatibilityCategory.POTENTIALLY_BREAKING,
    "operation-removed": CompatibilityCategory.BREAKING,
    "request-required-field-added": CompatibilityCategory.BREAKING,
    "request-field-removed": CompatibilityCategory.BREAKING,
    "response-required-field-removed": CompatibilityCategory.BREAKING,
    "response-field-type-changed": CompatibilityCategory.BREAKING,
    "deprecation-window-violation": CompatibilityCategory.BREAKING,
    "deprecation-window-satisfied": CompatibilityCategory.NON_BREAKING,
    "release-state-invalid": CompatibilityCategory.POTENTIALLY_BREAKING,
    "baseline-ref-applied": CompatibilityCategory.NON_BREAKING,
    "baseline-missing": CompatibilityCategory.BREAKING,
    "baseline-invalid": CompatibilityCategory.BREAKING,
}
DEFAULT_COMPATIBILITY_TAXONOMY: Mapping[str, CompatibilityCategory] = MappingProxyType(
    _DEFAULT_COMPATIBILITY_TAXONOMY
)


@dataclass(slots=True, frozen=True)
class CompatibilityChange:
    code: str
    location: str
    detail: str = ""


@dataclass(slots=True, frozen=True)
class ClassifiedCompatibilityChange:
    category: CompatibilityCategory
    code: str
    location: str
    detail: str = ""


@dataclass(slots=True, frozen=True)
class CompatibilityReport:
    overall: CompatibilityCategory
    counts: dict[CompatibilityCategory, int]
    items: tuple[ClassifiedCompatibilityChange, ...]


def classify_change(
    code: str,
    taxonomy: Mapping[str, CompatibilityCategory] | None = None,
) -> CompatibilityCategory:
    active_taxonomy = taxonomy or DEFAULT_COMPATIBILITY_TAXONOMY
    return active_taxonomy.get(code, CompatibilityCategory.POTENTIALLY_BREAKING)


def classify_changes(
    changes: Iterable[CompatibilityChange],
    taxonomy: Mapping[str, CompatibilityCategory] | None = None,
) -> CompatibilityReport:
    items = tuple(
        ClassifiedCompatibilityChange(
            category=classify_change(change.code, taxonomy=taxonomy),
            code=change.code,
            location=change.location,
            detail=change.detail,
        )
        for change in changes
    )

    ordered_items = tuple(
        sorted(
            items,
            key=lambda item: (
                _severity_rank(item.category),
                item.code,
                item.location,
                item.detail,
            ),
        )
    )

    counts = {
        CompatibilityCategory.NON_BREAKING: 0,
        CompatibilityCategory.POTENTIALLY_BREAKING: 0,
        CompatibilityCategory.BREAKING: 0,
    }
    for item in ordered_items:
        counts[item.category] += 1

    if counts[CompatibilityCategory.BREAKING] > 0:
        overall = CompatibilityCategory.BREAKING
    elif counts[CompatibilityCategory.POTENTIALLY_BREAKING] > 0:
        overall = CompatibilityCategory.POTENTIALLY_BREAKING
    else:
        overall = CompatibilityCategory.NON_BREAKING

    return CompatibilityReport(overall=overall, counts=counts, items=ordered_items)


def _severity_rank(category: CompatibilityCategory) -> int:
    if category == CompatibilityCategory.BREAKING:
        return 0
    if category == CompatibilityCategory.POTENTIALLY_BREAKING:
        return 1
    return 2
