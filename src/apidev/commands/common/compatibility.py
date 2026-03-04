import typer
from typer.models import OptionInfo
from rich.console import Console
from typing import cast

from apidev.application.dto.diagnostics import sort_diagnostics
from apidev.application.dto.generation_plan import CompatibilityPolicy


def parse_compatibility_policy(policy: object) -> str | None:
    current = policy
    for _ in range(8):
        if isinstance(current, OptionInfo):
            current = current.default
            continue
        if current is None:
            return None
        if isinstance(current, str):
            break
        if hasattr(current, "default"):
            default = getattr(current, "default")
            if default is current:
                break
            current = default
            continue
        break

    if current is None:
        return None
    normalized = str(current).strip().lower()
    if normalized in {"warn", "strict"}:
        return normalized
    raise typer.BadParameter(
        f"Invalid compatibility policy '{current}'. Expected one of: warn, strict."
    )


def resolve_compatibility_policy(cli_policy: str | None, config_policy: str) -> CompatibilityPolicy:
    current: object = cli_policy if cli_policy is not None else config_policy
    for _ in range(8):
        if current is None:
            return "warn"
        if isinstance(current, str):
            normalized = parse_compatibility_policy(current) or "warn"
            if normalized in {"warn", "strict"}:
                return cast(CompatibilityPolicy, normalized)
        if hasattr(current, "default"):
            current = getattr(current, "default")
            continue
        break
    value = str(current).strip().lower()
    raise ValueError(f"Invalid compatibility policy '{value}'. Expected one of: warn, strict.")


def print_compatibility(console: Console, policy: str, compatibility: object) -> None:
    overall = str(getattr(compatibility, "overall", "non-breaking"))
    counts = _normalize_compatibility_counts(getattr(compatibility, "counts", {}))
    diagnostics = _sorted_compatibility_entries(getattr(compatibility, "diagnostics", []))

    console.print(f"Compatibility policy: {policy}")
    console.print(
        "Compatibility overall: "
        f"{overall} "
        f"(breaking={counts.get('breaking', 0)}, "
        f"potentially-breaking={counts.get('potentially-breaking', 0)}, "
        f"non-breaking={counts.get('non-breaking', 0)})"
    )

    for diagnostic in diagnostics:
        category = (
            str(getattr(diagnostic, "category", "potentially-breaking")).upper().replace("-", "_")
        )
        code = str(getattr(diagnostic, "code", "unknown"))
        location = str(getattr(diagnostic, "location", "unknown"))
        detail = str(getattr(diagnostic, "detail", ""))
        suffix = f" ({detail})" if detail else ""
        console.print(f"COMPATIBILITY_{category} {code} at {location}{suffix}")


def build_compatibility_payload(
    *,
    policy: str,
    compatibility: object,
    source: str = "diff-service",
) -> dict[str, object]:
    diagnostics = compatibility_diagnostics_unified(
        compatibility=compatibility,
        source=source,
    )
    return {
        "policy": policy,
        "overall": str(getattr(compatibility, "overall", "non-breaking")),
        "counts": _normalize_compatibility_counts(getattr(compatibility, "counts", {})),
        "diagnostics": diagnostics,
    }


def compatibility_diagnostics_unified(
    *,
    compatibility: object,
    source: str = "diff-service",
) -> list[dict[str, object]]:
    entries = _sorted_compatibility_entries(getattr(compatibility, "diagnostics", []))
    diagnostics = [
        _serialize_compatibility_diagnostic(diagnostic=entry, source=source) for entry in entries
    ]
    return sort_diagnostics(diagnostics)


def _serialize_compatibility_diagnostic(
    *,
    diagnostic: object,
    source: str,
) -> dict[str, object]:
    code = str(getattr(diagnostic, "code", "compatibility.unknown"))
    location = str(getattr(diagnostic, "location", "unknown"))
    detail = str(getattr(diagnostic, "detail", ""))
    severity = _compatibility_severity(str(getattr(diagnostic, "category", "potentially-breaking")))
    payload: dict[str, object] = {
        "code": code,
        "severity": severity,
        "location": location,
        "message": f"Compatibility diagnostic: {code}",
        "category": "compatibility",
        "source": source,
    }
    if detail:
        payload["detail"] = detail
    return payload


def _normalize_compatibility_counts(raw_counts: object) -> dict[str, int]:
    counts = raw_counts if isinstance(raw_counts, dict) else {}
    return {
        "non-breaking": int(counts.get("non-breaking", 0)),
        "potentially-breaking": int(counts.get("potentially-breaking", 0)),
        "breaking": int(counts.get("breaking", 0)),
    }


def _compatibility_severity(category: str) -> str:
    normalized = category.strip().lower()
    if normalized == "breaking":
        return "error"
    if normalized == "potentially-breaking":
        return "warning"
    return "info"


def _severity_rank(severity: str) -> int:
    if severity == "error":
        return 0
    if severity == "warning":
        return 1
    return 2


def _sorted_compatibility_entries(entries: object) -> list[object]:
    if not isinstance(entries, list):
        return []
    return sorted(
        entries,
        key=lambda entry: (
            _severity_rank(_compatibility_severity(str(getattr(entry, "category", "info")))),
            str(getattr(entry, "code", "")),
            str(getattr(entry, "location", "")),
            str(getattr(entry, "detail", "")),
        ),
    )
