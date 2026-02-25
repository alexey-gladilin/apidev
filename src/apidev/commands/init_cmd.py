from pathlib import Path

from rich.console import Console

from apidev.application.services.init_service import InitService
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem

console = Console()


def init_command(project_dir: Path = Path(".")) -> None:
    service = InitService(fs=LocalFileSystem())
    created = service.run(project_dir.resolve())
    console.print(f"Initialized .apidev workspace. Created/updated files: {created}")
