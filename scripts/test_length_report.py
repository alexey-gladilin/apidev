"""
Report large test files and test functions (non-blocking).
Used by make test-length-report to surface potential test maintainability issues.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT / "tests"
FILE_LINE_THRESHOLD = 200
FUNC_LINE_THRESHOLD = 50


def count_file_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except Exception:
        return 0


def get_test_functions_and_lines(path: Path) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return result
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            line_count = (node.end_lineno or node.lineno) - node.lineno + 1
            result.append((node.name, line_count))
    return result


def main() -> int:
    if not TESTS_DIR.is_dir():
        print(f"Tests directory not found: {TESTS_DIR}", file=sys.stderr)
        return 0  # non-blocking

    large_files: list[tuple[str, int]] = []
    large_functions: list[tuple[str, str, int]] = []

    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        lines = count_file_lines(path)
        if lines >= FILE_LINE_THRESHOLD:
            large_files.append((str(rel), lines))
        for name, func_lines in get_test_functions_and_lines(path):
            if func_lines >= FUNC_LINE_THRESHOLD:
                large_functions.append((str(rel), name, func_lines))

    print("Test length report (non-blocking)")
    print("----------------------------------")
    if large_files:
        print(f"\nFiles with >={FILE_LINE_THRESHOLD} lines:")
        for rel, lines in sorted(large_files, key=lambda x: -x[1]):
            print(f"  {rel}: {lines} lines")
    else:
        print(f"\nNo test files with >={FILE_LINE_THRESHOLD} lines.")

    if large_functions:
        print(f"\nTest functions with >={FUNC_LINE_THRESHOLD} lines:")
        for rel, name, lines in sorted(large_functions, key=lambda x: -x[2]):
            print(f"  {rel}::{name}: {lines} lines")
    else:
        print(f"\nNo test functions with >={FUNC_LINE_THRESHOLD} lines.")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
