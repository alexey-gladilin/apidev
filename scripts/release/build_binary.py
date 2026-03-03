from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    dist_dir = Path("dist/bin")
    work_dir = Path("build/pyinstaller")
    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

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
            "-m",
            "apidev.cli",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(work_dir),
            "--specpath",
            str(work_dir),
        ]
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
