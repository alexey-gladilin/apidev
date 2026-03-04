from pathlib import Path
from typing import Annotated, Literal
import tomllib

import typer
import tomli_w

_ALLOWED_RUNTIMES = ("fastapi", "none")
_ALLOWED_INTEGRATION_MODES = ("off", "scaffold", "full")
InitMode = Literal["create", "repair", "force"]
RuntimeProfile = Literal["fastapi", "none"]
IntegrationMode = Literal["off", "scaffold", "full"]


def _normalize_text_option(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _validate_profile_options(
    runtime: object, integration_mode: object
) -> tuple[RuntimeProfile, IntegrationMode]:
    runtime_value = _normalize_text_option(runtime)
    integration_mode_value = _normalize_text_option(integration_mode)

    if runtime_value not in _ALLOWED_RUNTIMES:
        raise typer.BadParameter(
            "config.INIT_PROFILE_INVALID_ENUM: --runtime must be one of: fastapi, none."
        )
    if integration_mode_value not in _ALLOWED_INTEGRATION_MODES:
        raise typer.BadParameter(
            "config.INIT_PROFILE_INVALID_ENUM: --integration-mode must be one of: off, scaffold, full."
        )
    if runtime_value == "none" and integration_mode_value == "full":
        raise typer.BadParameter(
            "config.INIT_MODE_CONFLICT: --integration-mode full requires --runtime fastapi."
        )
    runtime_profile: RuntimeProfile = "fastapi" if runtime_value == "fastapi" else "none"
    if integration_mode_value == "off":
        integration_mode_profile: IntegrationMode = "off"
    elif integration_mode_value == "scaffold":
        integration_mode_profile = "scaffold"
    else:
        integration_mode_profile = "full"
    return runtime_profile, integration_mode_profile


def _validate_integration_dir(project_root: Path, integration_dir: object) -> None:
    integration_dir_value = _normalize_text_option(integration_dir)
    if not integration_dir_value:
        raise typer.BadParameter(
            "validation.PATH_BOUNDARY_VIOLATION: --integration-dir must be a non-empty relative path inside project_dir."
        )
    integration_candidate = Path(integration_dir_value)
    if integration_candidate.is_absolute():
        raise typer.BadParameter(
            "validation.PATH_BOUNDARY_VIOLATION: --integration-dir must be a non-empty relative path inside project_dir."
        )
    resolved_integration_dir = (project_root / integration_candidate).resolve(strict=False)
    try:
        resolved_integration_dir.relative_to(project_root)
    except ValueError as exc:
        raise typer.BadParameter(
            "validation.PATH_BOUNDARY_VIOLATION: --integration-dir must stay inside project_dir."
        ) from exc


def _profile_default_config_text(base_text: str, integration_dir: str) -> str:
    data = tomllib.loads(base_text)
    generator_section = data.setdefault("generator", {})
    if not isinstance(generator_section, dict):
        raise typer.BadParameter("Invalid default config shape for [generator] section.")
    generator_section["scaffold_dir"] = integration_dir
    return tomli_w.dumps(data)


def init_command(
    project_dir: Path = Path("."),
    repair: Annotated[
        bool,
        typer.Option(
            "--repair",
            help="Repair missing/invalid init-managed files (does not overwrite valid ones).",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite all init-managed files with defaults.",
        ),
    ] = False,
    runtime: Annotated[
        str,
        typer.Option(
            "--runtime",
            metavar="[fastapi|none]",
            help="Integration runtime profile.",
        ),
    ] = "fastapi",
    integration_mode: Annotated[
        str,
        typer.Option(
            "--integration-mode",
            metavar="[off|scaffold|full]",
            help="Integration bootstrap mode.",
        ),
    ] = "scaffold",
    integration_dir: Annotated[
        str,
        typer.Option(
            "--integration-dir",
            help="Integration directory (must stay inside project directory).",
        ),
    ] = "integration",
) -> None:
    from rich.console import Console

    from apidev.application.services.init_service import (
        InitPathBoundaryError,
        InitRepairRequiredError,
        InitService,
    )
    from apidev.infrastructure.config.toml_loader import default_config_text
    from apidev.infrastructure.filesystem.local_fs import LocalFileSystem

    console = Console()

    if repair and force:
        raise typer.BadParameter("Use either --repair or --force, not both.")
    project_root = project_dir.resolve()
    runtime_profile, integration_mode_profile = _validate_profile_options(
        runtime=runtime, integration_mode=integration_mode
    )
    _validate_integration_dir(project_root=project_root, integration_dir=integration_dir)
    integration_dir_value = _normalize_text_option(integration_dir)

    mode: InitMode = "create"
    if repair:
        mode = "repair"
    elif force:
        mode = "force"

    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=_profile_default_config_text(
            base_text=default_config_text(),
            integration_dir=integration_dir_value,
        ),
    )
    try:
        result = service.run(
            project_root,
            mode=mode,
            runtime=runtime_profile,
            integration_mode=integration_mode_profile,
        )
    except InitPathBoundaryError as exc:
        console.print(f"[red]ERROR[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except InitRepairRequiredError as exc:
        console.print(
            "[red]ERROR[/red] Project has invalid init-managed file(s). "
            "Run `apidev init --repair` or `apidev init --force`."
        )
        for path in exc.invalid_paths:
            console.print(f"  - {path}")
        raise typer.Exit(code=1) from exc

    if result.status == "already_initialized":
        console.print("Project already initialized.")
        return
    if result.status == "repaired":
        console.print("Project repaired successfully.")
        return
    if result.status == "forced":
        console.print("Project init files overwritten successfully.")
        return

    console.print("Project initialized successfully.")
