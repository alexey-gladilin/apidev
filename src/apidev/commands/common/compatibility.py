import typer
from rich.console import Console


def parse_compatibility_policy(policy: str | None) -> str | None:
    if policy is None:
        return None
    normalized = str(policy).strip().lower()
    if normalized in {"warn", "strict"}:
        return normalized
    raise typer.BadParameter(
        f"Invalid compatibility policy '{policy}'. Expected one of: warn, strict."
    )


def resolve_compatibility_policy(cli_policy: str | None, config_policy: str) -> str:
    return cli_policy if cli_policy is not None else parse_compatibility_policy(config_policy) or "warn"


def print_compatibility(console: Console, policy: str, compatibility: object) -> None:
    overall = str(getattr(compatibility, "overall", "non-breaking"))
    counts = getattr(compatibility, "counts", {})
    diagnostics = getattr(compatibility, "diagnostics", [])

    console.print(f"Compatibility policy: {policy}")
    console.print(
        "Compatibility overall: "
        f"{overall} "
        f"(breaking={counts.get('breaking', 0)}, "
        f"potentially-breaking={counts.get('potentially-breaking', 0)}, "
        f"non-breaking={counts.get('non-breaking', 0)})"
    )

    for diagnostic in diagnostics:
        category = str(getattr(diagnostic, "category", "potentially-breaking")).upper().replace(
            "-", "_"
        )
        code = str(getattr(diagnostic, "code", "unknown"))
        location = str(getattr(diagnostic, "location", "unknown"))
        detail = str(getattr(diagnostic, "detail", ""))
        suffix = f" ({detail})" if detail else ""
        console.print(f"COMPATIBILITY_{category} {code} at {location}{suffix}")
