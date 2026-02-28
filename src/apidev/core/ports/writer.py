from pathlib import Path
from typing import Protocol


class WriterPort(Protocol):
    def write(self, generated_root: Path, target: Path, content: str) -> None: ...

    def remove(self, generated_root: Path, target: Path) -> bool: ...
