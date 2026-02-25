"""AR-006: writer enforces generated-root boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.writer import SafeWriter


def test_writer_allows_write_inside_generated_root(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    generated_root = tmp_path / "generated"
    target = generated_root / "routers" / "sample.py"

    writer.write(generated_root, target, "x = 1\n")

    assert target.read_text(encoding="utf-8") == "x = 1\n"


def test_writer_rejects_write_outside_generated_root(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    generated_root = tmp_path / "generated"
    target = tmp_path / "manual" / "unsafe.py"

    with pytest.raises(ValueError, match="Refusing to write outside generated root"):
        writer.write(generated_root, target, "x = 1\n")


def test_writer_rejects_write_to_root_path_itself(tmp_path: Path) -> None:
    writer = SafeWriter(fs=LocalFileSystem())
    generated_root = tmp_path / "generated"

    with pytest.raises(ValueError, match="Refusing to write to generated root path directly"):
        writer.write(generated_root, generated_root, "x = 1\n")
