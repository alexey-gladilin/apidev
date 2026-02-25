from pathlib import Path

from rich.console import Console

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

console = Console()


def diff_command(project_dir: Path = Path(".")) -> None:
    root = project_dir.resolve()
    service = DiffService(
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(project_dir=root),
        fs=LocalFileSystem(),
    )
    plan = service.run(root)

    if not plan.changes:
        console.print("No changes")
        return

    for change in plan.changes:
        console.print(f"{change.change_type:>7} {change.path}")
