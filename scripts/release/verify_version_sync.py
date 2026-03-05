#!/usr/bin/env python3
"""Verify release version matches project metadata version sources."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import tomllib


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_pyproject_version(root: Path) -> str:
    pyproject_path = root / "pyproject.toml"
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = payload.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml: [project] section is missing")
    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml: project.version must be a non-empty string")
    return version.strip()


def _read_init_version(root: Path) -> str:
    init_path = root / "src" / "apidev" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    dynamic_assignment = re.search(
        r"^__version__\s*=\s*_resolve_package_version\(\)\s*$", text, flags=re.MULTILINE
    )
    if dynamic_assignment:
        return _read_pyproject_version(root)

    raise ValueError(
        "src/apidev/__init__.py: expected '__version__ = _resolve_package_version()'"
    )


def _normalize_release_version(raw_version: str) -> str:
    normalized = raw_version.strip()
    if normalized.startswith("v"):
        normalized = normalized[1:]
    if not normalized:
        raise ValueError("release version must be non-empty")
    return normalized


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check release version consistency")
    parser.add_argument(
        "--release-version",
        required=True,
        help="Release version from CI/tag (SemVer, optional leading 'v').",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = _project_root()
    normalized_release_version = _normalize_release_version(str(args.release_version))
    pyproject_version = _read_pyproject_version(root)
    init_version = _read_init_version(root)

    if pyproject_version != init_version:
        raise ValueError(
            "Version mismatch between pyproject.toml and src/apidev/__init__.py: "
            f"{pyproject_version!r} != {init_version!r}"
        )
    if normalized_release_version != pyproject_version:
        raise ValueError(
            "Release version does not match project version: "
            f"release={normalized_release_version!r}, project={pyproject_version!r}"
        )

    print(f"Version sync OK: {normalized_release_version}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"Version sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
