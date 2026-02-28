"""Shared baseline-ref parsing and resolution for CLI commands."""

import typer
from typer.models import OptionInfo

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
    if isinstance(value, OptionInfo):
        return parse_baseline_ref(value.default)
    return parse_baseline_ref(value if isinstance(value, str) else None)
