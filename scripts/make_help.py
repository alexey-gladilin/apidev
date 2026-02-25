"""
Cross-platform Makefile parser for generating help messages.
Replaces awk for Windows compatibility.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = ROOT / "Makefile"


def parse_makefile_help() -> None:
    """Parses Makefile and outputs formatted help."""
    if not MAKEFILE.exists():
        print("Makefile not found", file=sys.stderr)
        sys.exit(1)

    content = MAKEFILE.read_text(encoding="utf-8")
    lines = content.split("\n")

    # ANSI colors
    YELLOW = "\033[1;33m"
    GREEN = "\033[0;32m"
    NC = "\033[0m"

    current_section = None

    for line in lines:
        # Section handling (##@)
        section_match = re.match(r"^##@\s*(.+)$", line)
        if section_match:
            current_section = section_match.group(1).strip()
            print(f"\n{GREEN}{current_section}{NC}")
            continue

        # Command handling (target: ## description)
        cmd_match = re.match(r"^([A-Za-z0-9_.-]+):\s*##\s*(.+)$", line)
        if cmd_match:
            target = cmd_match.group(1)
            description = cmd_match.group(2)
            print(f"  {YELLOW}{target:<20}{NC} {description}")


if __name__ == "__main__":
    parse_makefile_help()
