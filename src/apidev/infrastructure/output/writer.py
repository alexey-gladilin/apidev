from pathlib import Path

from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.writer import WriterPort


class SafeWriter(WriterPort):
    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    def write(self, generated_root: Path, target: Path, content: str) -> None:
        root = generated_root.resolve()
        final = target.resolve()

        if root == final:
            raise ValueError("Refusing to write to generated root path directly")

        if root not in final.parents:
            raise ValueError(f"Refusing to write outside generated root: {final}")

        self.fs.write_text(final, content)
