"""
Interactive menu for Makefile commands using InquirerPy and Rich.

Supports macOS, Windows, and Linux. Falls back to numeric prompt
if InquirerPy is not installed.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
    from InquirerPy.separator import Separator
    from InquirerPy.utils import get_style

    INQUIRER_AVAILABLE = True
except Exception:
    inquirer = None
    Choice = None
    Separator = None
    get_style = None
    INQUIRER_AVAILABLE = False

try:
    from rich.console import Console

    RICH_AVAILABLE = True
    console: Console | None = Console(force_terminal=True)
except Exception:
    RICH_AVAILABLE = False
    console = None

ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = ROOT / "Makefile"


def fail(msg: str) -> None:
    """Log an error and exit."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_makefile() -> List[Dict[str, Optional[str]]]:
    """Parse Makefile targets and sections for help/menu."""
    if not MAKEFILE.exists():
        fail(f"Makefile not found at {MAKEFILE}")

    commands: List[Dict[str, Optional[str]]] = []
    current_section: Optional[str] = None

    for raw in MAKEFILE.read_text(encoding="utf-8").splitlines():
        section_match = re.match(r"^##@\s*(.+)$", raw)
        if section_match:
            current_section = section_match.group(1).strip()
            continue

        cmd_match = re.match(r"^([A-Za-z0-9_.-]+):\s*##\s*(.+)$", raw)
        if cmd_match:
            commands.append(
                {
                    "target": cmd_match.group(1),
                    "description": cmd_match.group(2),
                    "section": current_section,
                }
            )

    return commands


def extract_title() -> str:
    """Read project title from Makefile echo or use root dir name."""
    content = MAKEFILE.read_text(encoding="utf-8")
    for raw in content.splitlines():
        if "echo" not in raw:
            continue
        # Match "apidev — ..." style titles
        for pattern in (r"apidev[^$\"']+",):
            match = re.search(pattern, raw)
            if match:
                return match.group(0).strip()
    return ROOT.name.replace("-", " ").title()


def print_intro(title: str) -> None:
    """Print header before command list."""
    if console:
        console.print()
        console.print(f"[blue]{title}[/]")
        console.print()
        console.print("[green]Main commands:[/]")
    else:
        print()
        print(title)
        print()
        print("Main commands:")


def format_command(cmd: Dict[str, Optional[str]]) -> str:
    """Format a single command line for display."""
    target = cmd["target"] or ""
    description = cmd["description"] or ""
    return f"{target:<20} {description}"


def build_choices(commands: List[Dict[str, Optional[str]]]) -> list | None:
    """Build InquirerPy choices grouped by section."""
    if not INQUIRER_AVAILABLE or Separator is None or Choice is None:
        return None

    choices: list = []
    last_section: Optional[str] = None

    for cmd in commands:
        section_label = cmd["section"] or "Main commands"
        if section_label != last_section:
            if choices:
                choices.append(Separator(""))
            choices.append(Separator(section_label))
            last_section = section_label
        target = cmd["target"]
        if target:
            choices.append(Choice(value=target, name=format_command(cmd)))
    return choices


def prompt_command(commands: List[Dict[str, Optional[str]]]) -> Optional[str]:
    """Prompt user to select a command."""
    if INQUIRER_AVAILABLE and inquirer is not None and get_style is not None:
        choices = build_choices(commands)
        if not choices:
            fail("No commands available for selection.")

        style = get_style(
            {
                "question": "green",
                "separator": "green",
                "pointer": "#61afef bold",
                "answer": "yellow",
                "questionmark": "#e5c07b",
            },
            style_override=False,
        )

        result = inquirer.select(  # type: ignore[attr-defined,arg-type]
            message="Select command to run",
            choices=choices,  # type: ignore[arg-type]
            pointer="›",
            qmark="👉",
            cycle=True,
            style=style,
        ).execute()
        return result

    # Fallback: numeric selection
    install_hint = (
        "InquirerPy / rich are not installed. "
        "For full interactive mode install in the project venv:\n"
        "  source .venv/bin/activate && pip install InquirerPy rich\n"
        "  or: uv pip install InquirerPy rich\n"
    )
    if console:
        console.print(install_hint)
        console.print("Falling back to numeric selection.")
    else:
        print(install_hint)
        print("Falling back to numeric selection.")

    indexed: List[str] = []
    last_section: Optional[str] = None
    counter = 1
    for cmd in commands:
        section_label = cmd["section"] or "Main commands"
        if section_label != last_section:
            if console:
                console.print(f"\n[green]{section_label}[/]")
            else:
                print(f"\n{section_label}")
            last_section = section_label
        target = cmd["target"]
        if target:
            if console:
                console.print(
                    f"  [{counter}] [yellow]{target:<20}[/] {cmd['description']}"
                )
            else:
                print(f"  [{counter}] {format_command(cmd)}")
            indexed.append(target)
        counter += 1

    while True:
        choice = input("\nEnter number (blank to exit): ").strip()
        if not choice:
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(indexed):
                return indexed[idx - 1]
        print("Invalid selection, try again.")


def run_make(target: str) -> int:
    """Execute the selected make target."""
    make_cmd = os.environ.get("MAKE", "make")
    result = subprocess.run([make_cmd, target], cwd=ROOT, env=os.environ)
    return result.returncode


def main() -> None:
    commands = parse_makefile()
    if not commands:
        fail("No commands found in Makefile.")

    title = extract_title()
    print_intro(title)

    selection = prompt_command(commands)
    if not selection:
        if console:
            console.print("No command selected. Exit.")
        else:
            print("No command selected. Exit.")
        return

    exit_code = run_make(selection)
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if console:
            console.print("\nInterrupted by user.")
        else:
            print("\nInterrupted by user.")
        sys.exit(0)
