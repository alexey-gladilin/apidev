from __future__ import annotations

import argparse
import os
import platform
import re
import sys
import tarfile
import zipfile
from pathlib import Path

_RUNNER_INPUT_PATTERN = re.compile(r"^[A-Za-z0-9 _-]+$")
_ARCHIVE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

_RUNNER_OS_ALIASES = {
    "linux": "linux",
    "windows": "windows",
    "win32": "windows",
    "macos": "macos",
    "darwin": "macos",
}

_RUNNER_ARCH_ALIASES = {
    "x64": "x64",
    "x8664": "x64",
    "amd64": "x64",
    "arm64": "arm64",
    "aarch64": "arm64",
}


def _default_binary_path() -> Path:
    executable_name = "apidev.exe" if sys.platform.startswith("win") else "apidev"
    return Path("dist/bin") / executable_name


def _default_onedir_dir_path() -> Path:
    return Path("dist/bin") / "apidev"


def _normalize_runner_value(name: str, value: str, aliases: dict[str, str]) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if not _RUNNER_INPUT_PATTERN.fullmatch(value):
        raise ValueError(f"{name} contains unsafe characters: {value!r}")

    compact = re.sub(r"[^a-z0-9]+", "", value.lower())
    normalized = aliases.get(compact)
    if normalized is None:
        allowed = ", ".join(sorted(set(aliases.values())))
        raise ValueError(f"{name} must be one of: {allowed}. Got: {value!r}")
    return normalized


def _validate_archive_name_override(archive_name: str) -> str:
    if not isinstance(archive_name, str) or not archive_name.strip():
        raise ValueError("archive_name must be a non-empty string")
    if archive_name != Path(archive_name).name:
        raise ValueError("archive_name must be a plain file name without path segments")
    if ".." in archive_name:
        raise ValueError("archive_name must not contain parent directory traversal sequences")
    if not _ARCHIVE_NAME_PATTERN.fullmatch(archive_name):
        raise ValueError("archive_name contains unsupported characters")
    if not (archive_name.endswith(".zip") or archive_name.endswith(".tar.gz")):
        raise ValueError("archive_name must end with .zip or .tar.gz")
    return archive_name


def _resolve_archive_name(
    runner_os: str,
    runner_arch: str,
    archive_name_override: str | None,
    release_version: str | None = None,
    mode: str = "onefile",
) -> str:
    os_name = _normalize_runner_value("runner_os", runner_os, _RUNNER_OS_ALIASES)
    arch = _normalize_runner_value("runner_arch", runner_arch, _RUNNER_ARCH_ALIASES)

    if mode not in {"onefile", "onedir"}:
        raise ValueError(f"Unsupported mode: {mode}")

    if archive_name_override is not None:
        return _validate_archive_name_override(archive_name_override)

    if release_version is not None:
        if not isinstance(release_version, str) or not release_version.strip():
            raise ValueError("release version must be a non-empty string")
        if not _VERSION_PATTERN.fullmatch(release_version):
            raise ValueError("release version contains unsupported characters")
        if mode == "onedir":
            return f"apidev-{release_version}-{os_name}-{arch}-onedir.tar.gz"
        if os_name == "windows":
            return f"apidev-{release_version}-{os_name}-{arch}.zip"
        return f"apidev-{release_version}-{os_name}-{arch}.tar.gz"

    if mode == "onedir":
        return f"apidev-{os_name}-{arch}-onedir.tar.gz"
    if os_name == "windows":
        return f"apidev-{os_name}-{arch}.zip"
    return f"apidev-{os_name}-{arch}.tar.gz"


def _default_archive_name(
    runner_os: str, runner_arch: str, release_version: str | None, mode: str
) -> str:
    return _resolve_archive_name(runner_os, runner_arch, None, release_version, mode=mode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary-path", type=Path, default=_default_binary_path())
    parser.add_argument("--output-dir", type=Path, default=Path("dist/release"))
    parser.add_argument("--runner-os", default=os.environ.get("RUNNER_OS", sys.platform))
    parser.add_argument("--runner-arch", default=os.environ.get("RUNNER_ARCH", platform.machine()))
    parser.add_argument("--archive-name", default=None)
    parser.add_argument("--version", default=os.environ.get("RELEASE_VERSION"))
    parser.add_argument(
        "--mode",
        choices=["onefile", "onedir"],
        default="onefile",
        help="Artifact mode to package",
    )
    parser.add_argument(
        "--onedir-path",
        type=Path,
        default=_default_onedir_dir_path(),
        help="Path to onedir output (used when --mode=onedir).",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_name = _resolve_archive_name(
        args.runner_os, args.runner_arch, args.archive_name, args.version, mode=args.mode
    )
    archive_path = args.output_dir / archive_name

    if args.mode == "onedir":
        if not args.onedir_path.is_dir():
            raise FileNotFoundError(f"Onedir artifact directory not found: {args.onedir_path}")
        with tarfile.open(archive_path, "w:gz") as tarred:
            tarred.add(args.onedir_path, arcname="apidev")
        return 0

    if not args.binary_path.exists():
        raise FileNotFoundError(f"Standalone binary not found: {args.binary_path}")

    binary_name = args.binary_path.name
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            zipped.write(args.binary_path, arcname=binary_name)
        return 0

    with tarfile.open(archive_path, "w:gz") as tarred:
        tarred.add(args.binary_path, arcname=binary_name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
