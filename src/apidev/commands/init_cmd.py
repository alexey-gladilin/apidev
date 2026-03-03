from pathlib import Path
from typing import Annotated

import typer


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
) -> None:
    from rich.console import Console

    from apidev.application.services.init_service import InitRepairRequiredError, InitService
    from apidev.infrastructure.config.toml_loader import default_config_text
    from apidev.infrastructure.filesystem.local_fs import LocalFileSystem

    console = Console()

    if repair and force:
        raise typer.BadParameter("Use either --repair or --force, not both.")

    mode = "create"
    if repair:
        mode = "repair"
    if force:
        mode = "force"

    service = InitService(fs=LocalFileSystem(), default_config_text=default_config_text())
    try:
        result = service.run(project_dir.resolve(), mode=mode)
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
