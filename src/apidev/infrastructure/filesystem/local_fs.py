from pathlib import Path

from apidev.core.ports.filesystem import FileSystemPort


class LocalFileSystem(FileSystemPort):
    def exists(self, path: Path) -> bool:
        return path.exists()

    def mkdir(self, path: Path, parents: bool = False) -> None:
        path.mkdir(parents=parents, exist_ok=True)

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def glob(self, root: Path, pattern: str) -> list[Path]:
        return sorted(root.glob(pattern))
