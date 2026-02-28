from pathlib import Path

from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.writer import WriterPort


class SafeWriter(WriterPort):
    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    def write(self, generated_root: Path, target: Path, content: str) -> None:
        final = self._resolve_within_generated_root(
            generated_root=generated_root,
            target=target,
            action="write",
            root_action_message="write to",
        )

        self.fs.write_text(final, content)

    def remove(self, generated_root: Path, target: Path) -> bool:
        final = self._resolve_within_generated_root(
            generated_root=generated_root,
            target=target,
            action="remove",
            root_action_message="remove",
        )

        if not final.exists():
            return False

        if final.is_dir():
            raise ValueError(f"Refusing to remove directory as generated artifact: {final}")

        final.unlink()
        return True

    def _resolve_within_generated_root(
        self,
        generated_root: Path,
        target: Path,
        action: str,
        root_action_message: str,
    ) -> Path:
        root = generated_root.resolve()
        final = target.resolve()

        if root == final:
            raise ValueError(f"Refusing to {root_action_message} generated root path directly")

        if root not in final.parents:
            raise ValueError(f"Refusing to {action} outside generated root: {final}")

        return final
