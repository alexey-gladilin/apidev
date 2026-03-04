from pathlib import Path
from typing import Protocol


class WriterPort(Protocol):
    def write(self, generated_dir_path: Path, target: Path, content: str) -> None: ...

    def remove(self, generated_dir_path: Path, target: Path) -> bool: ...
