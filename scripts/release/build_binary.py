from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Project root (parent of scripts/release/)
ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src"
CLI_SCRIPT = SRC / "apidev" / "cli.py"


def _run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd or ROOT)


def main() -> int:
    dist_dir = ROOT / "dist" / "bin"
    work_dir = ROOT / "build" / "pyinstaller"
    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    if not CLI_SCRIPT.exists():
        raise FileNotFoundError(f"CLI script not found: {CLI_SCRIPT}")

    _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            "apidev",
            "--paths",
            str(SRC),
            "--hidden-import",
            "typer",
            "--hidden-import",
            "click",
            str(CLI_SCRIPT),
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(work_dir),
            "--specpath",
            str(work_dir),
        ],
        cwd=ROOT,
    )

    binary_name = "apidev.exe" if sys.platform.startswith("win") else "apidev"
    binary_path = dist_dir / binary_name
    if not binary_path.exists():
        raise FileNotFoundError(
            f"Expected standalone binary at '{binary_path}' after build step"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
