from __future__ import annotations

import subprocess
import sys
import argparse
from pathlib import Path

# Project root (parent of scripts/release/)
ROOT = Path(__file__).resolve().parent.parent.parent
ONEFILE_SPEC_PATH = ROOT / "packaging" / "pyinstaller" / "apidev.spec"
ONEDIR_SPEC_PATH = ROOT / "packaging" / "pyinstaller" / "apidev_onedir.spec"


def _run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd or ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build standalone CLI binary")
    parser.add_argument(
        "--mode",
        choices=["onefile", "onedir"],
        default="onefile",
        help="PyInstaller output mode",
    )
    args = parser.parse_args()

    spec_path = ONEFILE_SPEC_PATH if args.mode == "onefile" else ONEDIR_SPEC_PATH

    dist_dir = ROOT / "dist" / "bin"
    work_dir = ROOT / "build" / "pyinstaller"
    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    if not spec_path.exists():
        raise FileNotFoundError(f"PyInstaller spec file not found: {spec_path}")

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
            str(spec_path),
        ],
        cwd=ROOT,
    )

    binary_name = "apidev.exe" if sys.platform.startswith("win") else "apidev"
    artifact_path = dist_dir / "apidev" if args.mode == "onedir" else dist_dir / binary_name
    if not artifact_path.exists():
        raise FileNotFoundError(f"Expected artifact at '{artifact_path}' after build step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
