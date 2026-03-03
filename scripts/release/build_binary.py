from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Project root (parent of scripts/release/)
ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_PATH = ROOT / "packaging" / "pyinstaller" / "apidev.spec"


def _run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd or ROOT)


def main() -> int:
    dist_dir = ROOT / "dist" / "bin"
    work_dir = ROOT / "build" / "pyinstaller"
    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"PyInstaller spec file not found: {SPEC_PATH}")

    _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(work_dir),
            str(SPEC_PATH),
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
