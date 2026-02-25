from pathlib import Path

from rich.console import Console

from apidev.application.services.diff_service import DiffService
from apidev.commands.runtime import load_runtime
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

console = Console()


def diff_command(project_dir: Path = Path(".")) -> None:
    root = project_dir.resolve()
    _, paths = load_runtime(root)
    fs = LocalFileSystem()
    service = DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=paths.templates_dir),
        fs=fs,
    )
    plan = service.run(root)

    if not plan.changes:
        console.print("No changes")
        return

    for change in plan.changes:
        console.print(f"{change.change_type:>7} {change.path}")
