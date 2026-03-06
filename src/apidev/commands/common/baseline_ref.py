"""Shared baseline-ref parsing and resolution for CLI commands."""

import typer

from apidev.commands.common.option_resolution import unwrap_option_default
from apidev.core.models.release_state import validate_baseline_ref


def parse_baseline_ref(value: str | None) -> str | None:
    """Parse and validate baseline-ref from CLI. Raises typer.BadParameter on invalid input."""
    if value is None:
        return None
    try:
        return validate_baseline_ref(value)
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid baseline ref '{value}'. {exc}") from exc


def resolve_baseline_ref(value: object) -> str | None:
    """Resolve baseline-ref from Typer option or raw value."""
    current = unwrap_option_default(value, max_depth=8)
    return parse_baseline_ref(current if isinstance(current, str) else None)
