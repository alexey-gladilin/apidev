from pathlib import Path

from apidev.core.ports.python_postprocessor import PythonPostprocessMode, PythonPostprocessorPort
from apidev.infrastructure.output.postprocess import format_python_content


class PythonPostprocessor(PythonPostprocessorPort):
    def format_python_content(
        self,
        project_dir: Path,
        target_path: Path,
        content: str,
        mode: PythonPostprocessMode,
    ) -> str:
        return format_python_content(
            project_dir=project_dir,
            target_path=target_path,
            content=content,
            mode=mode,
        )
