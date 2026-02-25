from pathlib import Path

from rich.console import Console

from apidev.application.services.init_service import InitService
from apidev.infrastructure.config.toml_loader import default_config_text
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem

console = Console()


def init_command(project_dir: Path = Path(".")) -> None:
    service = InitService(fs=LocalFileSystem(), default_config_text=default_config_text())
    created = service.run(project_dir.resolve())
    console.print(f"Initialized .apidev workspace. Created/updated files: {created}")
