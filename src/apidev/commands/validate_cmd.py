import json
from pathlib import Path

import typer
from rich.console import Console

from apidev.application.dto.diagnostics import (
    build_envelope,
    serialize_validation_diagnostic,
)
from apidev.application.services.validate_service import ValidateService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem

console = Console()


def validate_command(
    project_dir: Path = Path("."),
    json_output: bool = typer.Option(False, "--json", help="Print diagnostics as JSON."),
) -> None:
    root = project_dir.resolve()
    service = ValidateService(
        loader=YamlContractLoader(),
        config_loader=TomlConfigLoader(fs=LocalFileSystem()),
    )
    result = service.run(root)

    if json_output:
        payload = build_envelope(
            command="validate",
            mode="validate",
            diagnostics=[
                serialize_validation_diagnostic(diagnostic) for diagnostic in result.diagnostics
            ],
        )
        typer.echo(json.dumps(payload, ensure_ascii=False))
    elif result.diagnostics:
        for diagnostic in result.diagnostics:
            color = "red" if diagnostic.severity == "error" else "yellow"
            console.print(
                f"[{color}]{diagnostic.severity.upper()}[/{color}] "
                f"{diagnostic.code} {diagnostic.message} "
                f"({diagnostic.location}, rule={diagnostic.rule})"
            )
    else:
        console.print(f"Contracts valid. Operations: {len(result.operations)}")

    if result.has_errors:
        raise typer.Exit(code=1)
