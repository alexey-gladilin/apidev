from pathlib import Path

from rich.console import Console

from apidev.application.services.generate_service import GenerateService
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.writer import SafeWriter
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

console = Console()


def generate_command(project_dir: Path = Path("."), check: bool = False) -> None:
    root = project_dir.resolve()
    fs = LocalFileSystem()
    service = GenerateService(
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(project_dir=root),
        fs=fs,
        writer=SafeWriter(fs=fs),
    )
    result = service.run(root, check=check)

    if result.drift_detected:
        console.print("Drift detected")
        raise SystemExit(1)

    console.print(f"Applied changes: {result.applied_changes}")
