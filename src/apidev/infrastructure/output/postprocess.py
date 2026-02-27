from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Literal


PostprocessMode = Literal["auto", "none", "ruff", "black"]


@dataclass(slots=True)
class PostprocessResult:
    status: Literal["applied", "skipped", "failed"]
    message: str = ""


def format_python_content(
    project_dir: Path,
    target_path: Path,
    content: str,
    mode: PostprocessMode,
) -> str:
    if mode == "none":
        return content

    commands: list[list[str]]
    if mode == "auto":
        commands = [
            ["ruff", "format", "--stdin-filename", str(target_path), "-"],
            ["black", "--stdin-filename", str(target_path), "-"],
        ]
    elif mode == "ruff":
        commands = [["ruff", "format", "--stdin-filename", str(target_path), "-"]]
    else:
        commands = [["black", "--stdin-filename", str(target_path), "-"]]

    attempted: list[str] = []
    missing: list[str] = []

    for command in commands:
        executable = command[0]
        attempted.append(executable)
        if shutil.which(executable) is None:
            missing.append(executable)
            continue

        completed = subprocess.run(
            command,
            cwd=project_dir,
            input=content,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            return completed.stdout

        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown formatter error"
        if mode != "auto":
            raise ValueError(f"Postprocess failed for '{executable}': {stderr}")

    if mode == "auto":
        if missing and len(missing) == len(attempted):
            return content
        raise ValueError("Postprocess failed: available formatters returned non-zero exit code.")

    raise ValueError(f"Postprocess failed: formatter '{attempted[0]}' is not installed.")


def run_python_postprocess(
    project_dir: Path,
    changed_paths: list[Path],
    mode: PostprocessMode,
) -> PostprocessResult:
    if mode == "none":
        return PostprocessResult(status="skipped")

    python_files = sorted({str(path.resolve()) for path in changed_paths if path.suffix == ".py"})
    if not python_files:
        return PostprocessResult(status="skipped")

    commands: list[list[str]]
    if mode == "auto":
        commands = [["ruff", "format", *python_files], ["black", *python_files]]
    elif mode == "ruff":
        commands = [["ruff", "format", *python_files]]
    else:
        commands = [["black", *python_files]]

    attempted: list[str] = []
    missing: list[str] = []

    for command in commands:
        executable = command[0]
        attempted.append(executable)
        if shutil.which(executable) is None:
            missing.append(executable)
            continue

        completed = subprocess.run(
            command,
            cwd=project_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            return PostprocessResult(status="applied", message=f"Postprocess: {' '.join(command[:2])}")

        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown formatter error"
        if mode != "auto":
            return PostprocessResult(
                status="failed",
                message=f"Postprocess failed for '{executable}': {stderr}",
            )

    if mode == "auto":
        if missing and len(missing) == len(attempted):
            return PostprocessResult(
                status="skipped",
                message="Postprocess skipped: no formatter found (ruff/black).",
            )
        return PostprocessResult(
            status="failed",
            message="Postprocess failed: available formatters returned non-zero exit code.",
        )

    return PostprocessResult(
        status="failed",
        message=f"Postprocess failed: formatter '{attempted[0]}' is not installed.",
    )
