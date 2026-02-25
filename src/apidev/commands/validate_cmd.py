from pathlib import Path

import typer
from rich.console import Console

from apidev.application.services.validate_service import ValidateService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem

console = Console()


def validate_command(project_dir: Path = Path(".")) -> None:
    root = project_dir.resolve()
    service = ValidateService(
        loader=YamlContractLoader(),
        config_loader=TomlConfigLoader(fs=LocalFileSystem()),
    )
    result = service.run(root)

    if result.errors:
        for err in result.errors:
            console.print(f"[red]ERROR[/red] {err}")
        raise typer.Exit(code=1)

    console.print(f"Contracts valid. Operations: {len(result.operations)}")
