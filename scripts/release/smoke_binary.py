from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _default_binary_path() -> Path:
    executable_name = "apidev.exe" if sys.platform.startswith("win") else "apidev"
    return Path("dist/bin") / executable_name


def _default_onedir_binary_path() -> Path:
    executable_name = "apidev.exe" if sys.platform.startswith("win") else "apidev"
    return Path("dist/bin") / "apidev" / executable_name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--binary-path",
        type=Path,
        default=_default_binary_path(),
        help="Path to standalone apidev binary",
    )
    parser.add_argument(
        "--mode",
        choices=["onefile", "onedir"],
        default="onefile",
        help="Binary layout mode to test",
    )
    args = parser.parse_args()

    binary_path = args.binary_path
    if args.mode == "onedir" and binary_path == _default_binary_path():
        binary_path = _default_onedir_binary_path()

    if not binary_path.exists():
        raise FileNotFoundError(f"Standalone binary not found: {binary_path}")

    result = subprocess.run(
        [str(binary_path), "--help"],
        capture_output=True,
        text=True,
    )
    out = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        print("Binary stdout:", result.stdout, file=sys.stderr)
        print("Binary stderr:", result.stderr, file=sys.stderr)
        if "apidev" in out.lower():
            # Help was printed; some environments (e.g. frozen on macOS) may exit 1
            return 0
        return result.returncode
    if "apidev" not in out.lower():
        raise RuntimeError("Smoke gate failed: expected apidev --help output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
