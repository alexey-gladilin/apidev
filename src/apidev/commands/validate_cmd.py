from pathlib import Path

import typer
from rich.console import Console

from apidev.application.services.validate_service import ValidateService
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader

console = Console()


def validate_command(project_dir: Path = Path(".")) -> None:
    service = ValidateService(loader=YamlContractLoader())
    result = service.run(project_dir.resolve())

    if result.errors:
        for err in result.errors:
            console.print(f"[red]ERROR[/red] {err}")
        raise typer.Exit(code=1)

    console.print(f"Contracts valid. Operations: {len(result.operations)}")
