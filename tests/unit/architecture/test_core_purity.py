"""AR-003: core layer must not perform direct I/O or format parsing."""

from __future__ import annotations

import ast
from pathlib import Path


def _module_name(repo_root: Path, py_file: Path) -> str:
    rel = py_file.relative_to(repo_root / "src").with_suffix("")
    return ".".join(rel.parts)


def test_core_has_no_direct_io_or_format_parsing() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    src_root = repo_root / "src" / "apidev"
    offenders: list[str] = []
    forbidden_import_prefixes = ("tomllib", "yaml")
    forbidden_call_attrs = {"read_text", "write_text", "exists"}

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
                    if name.startswith(forbidden_import_prefixes):
                        offenders.append(
                            f"AR-003 | {py_file.relative_to(repo_root)}:{node.lineno} | "
                            f"forbidden import {name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(forbidden_import_prefixes):
                    offenders.append(
                        f"AR-003 | {py_file.relative_to(repo_root)}:{node.lineno} | "
                        f"forbidden import {module}"
                    )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    offenders.append(
                        f"AR-003 | {py_file.relative_to(repo_root)}:{node.lineno} | "
                        "forbidden call open(...)"
                    )
                elif (
                    isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_call_attrs
                ):
                    offenders.append(
                        f"AR-003 | {py_file.relative_to(repo_root)}:{node.lineno} | "
                        f"forbidden call .{node.func.attr}(...)"
                    )

    assert not offenders, "\n".join(sorted(offenders))
