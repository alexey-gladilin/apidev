"""AR-006: writer enforces project-root boundary for generated/scaffold artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.writer import SafeWriter


def test_writer_allows_write_inside_project_root(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    project_root = tmp_path
    target = project_root / "generated" / "routers" / "sample.py"

    writer.write(project_root, target, "x = 1\n")

    assert target.read_text(encoding="utf-8") == "x = 1\n"


def test_writer_allows_scaffold_write_inside_project_root(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    project_root = tmp_path
    target = project_root / "integration" / "handler_registry.py"

    writer.write(project_root, target, "x = 1\n")

    assert target.read_text(encoding="utf-8") == "x = 1\n"


def test_writer_rejects_write_outside_project_root(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    project_root = tmp_path
    target = tmp_path.parent / "unsafe.py"

    with pytest.raises(ValueError, match="Refusing to write outside generated root"):
        writer.write(project_root, target, "x = 1\n")


def test_writer_rejects_write_to_root_path_itself(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    project_root = tmp_path

    with pytest.raises(ValueError, match="Refusing to write to generated root path directly"):
        writer.write(project_root, project_root, "x = 1\n")


def test_writer_allows_remove_inside_project_root(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    project_root = tmp_path
    target = project_root / "generated" / "routers" / "stale.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("stale = True\n", encoding="utf-8")

    removed = writer.remove(project_root, target)

    assert removed is True
    assert not target.exists()


def test_writer_rejects_remove_outside_project_root(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    project_root = tmp_path
    target = tmp_path.parent / "unsafe.py"

    with pytest.raises(ValueError, match="Refusing to remove outside generated root"):
        writer.remove(project_root, target)
