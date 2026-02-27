from pathlib import Path
from typing import Literal, Protocol

PythonPostprocessMode = Literal["auto", "none", "ruff", "black"]


class PythonPostprocessorPort(Protocol):
    def format_python_content(
        self,
        project_dir: Path,
        target_path: Path,
        content: str,
        mode: PythonPostprocessMode,
    ) -> str: ...
