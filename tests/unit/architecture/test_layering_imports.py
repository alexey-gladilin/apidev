"""AR-001: core import layering guardrail."""

from __future__ import annotations

import ast
from pathlib import Path


def _module_name(repo_root: Path, py_file: Path) -> str:
    rel = py_file.relative_to(repo_root / "src").with_suffix("")
    return ".".join(rel.parts)


def test_core_does_not_import_outer_layers() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    src_root = repo_root / "src" / "apidev"
    forbidden = (
        "apidev.application",
        "apidev.commands",
        "apidev.infrastructure",
    )
    offenders: list[str] = []

    for py_file in sorted(src_root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue

        source_module = _module_name(repo_root, py_file)
        if not source_module.startswith("apidev.core."):
            continue

        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name.startswith(forbidden):
                        offenders.append(
                            f"AR-001 | {py_file.relative_to(repo_root)}:{node.lineno} | "
                            f"forbidden import {name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(forbidden):
                    offenders.append(
                        f"AR-001 | {py_file.relative_to(repo_root)}:{node.lineno} | "
                        f"forbidden import {module}"
                    )

    assert not offenders, "\n".join(sorted(offenders))
