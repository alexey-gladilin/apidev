from pathlib import Path

from apidev.core.path_boundary import (
    is_resolved_path_within_root,
    resolve_relative_path_within_root,
)


def test_resolve_relative_path_within_root_returns_resolved_path(tmp_path: Path) -> None:
    resolved = resolve_relative_path_within_root(tmp_path, ".apidev/release-state.json")

    assert resolved == (tmp_path / ".apidev" / "release-state.json").resolve(strict=False)


def test_resolve_relative_path_within_root_rejects_traversal(tmp_path: Path) -> None:
    assert resolve_relative_path_within_root(tmp_path, "../outside.json") is None


def test_is_resolved_path_within_root_handles_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    escaped = outside / "release-state.json"
    escaped.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(escaped)

    assert not is_resolved_path_within_root(link, tmp_path)
