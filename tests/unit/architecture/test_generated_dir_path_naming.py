"""AR-010: internal generated path naming must use generated_dir_path."""

from __future__ import annotations

import ast
from pathlib import Path


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def test_internal_generated_path_naming_is_unified() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    offenders: list[str] = []

    for base_dir in (repo_root / "src", repo_root / "tests"):
        for py_file in _iter_python_files(base_dir):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == "generated_root":
                    offenders.append(
                        f"AR-010 | {py_file.relative_to(repo_root)}:{node.lineno} | forbidden name generated_root"
                    )
                elif isinstance(node, ast.arg) and node.arg == "generated_root":
                    offenders.append(
                        f"AR-010 | {py_file.relative_to(repo_root)}:{node.lineno} | forbidden arg generated_root"
                    )
                elif isinstance(node, ast.Attribute) and node.attr == "generated_root":
                    offenders.append(
                        f"AR-010 | {py_file.relative_to(repo_root)}:{node.lineno} | forbidden attr generated_root"
                    )
                elif isinstance(node, ast.keyword) and node.arg == "generated_root":
                    offenders.append(
                        f"AR-010 | {py_file.relative_to(repo_root)}:{node.lineno} | forbidden kwarg generated_root"
                    )

    assert not offenders, "\n".join(sorted(offenders))
