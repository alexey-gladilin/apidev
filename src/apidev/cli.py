import sys
from pathlib import Path
import os
from typing import Callable, cast

from typer import Context, Exit, Option, Typer, echo
from apidev import __version__

from apidev.commands.diff_cmd import diff_command
from apidev.commands.generate_cmd import generate_command
from apidev.commands.graph_cmd import graph_command
from apidev.commands.init_cmd import init_command
from apidev.commands.validate_cmd import validate_command


def _fallback_shell_name_from_env() -> str | None:
    shell_path = os.environ.get("SHELL", "").strip()
    if shell_path:
        shell_name = Path(shell_path).name.lower()
        if shell_name in {"bash", "zsh", "fish", "pwsh", "powershell"}:
            return shell_name
        if shell_name == "sh":
            return "bash"
    if os.name == "nt":
        comspec = os.environ.get("COMSPEC", "").lower()
        if "powershell" in comspec:
            return "powershell"
        if comspec.endswith("cmd.exe"):
            return "cmd"
        return "powershell"
    return "bash"


def _safe_detect_shell_name(detector: Callable[[], str | None]) -> str | None:
    try:
        detected = detector()
        if detected:
            return detected
    except RuntimeError as exc:
        if "Shell detection not implemented for" not in str(exc):
            raise
    except ModuleNotFoundError as exc:
        if not (exc.name and exc.name.startswith("shellingham")):
            raise
    return _fallback_shell_name_from_env()


def _patch_typer_completion_shell_detection() -> None:
    import typer.completion as completion

    if getattr(completion, "_APIDEV_SHELL_PATCHED", False):
        return

    original_detector_obj = getattr(completion, "_get_shell_name", None)
    if not callable(original_detector_obj):
        return
    original_detector = cast(Callable[[], str | None], original_detector_obj)

    def _patched_detector() -> str | None:
        return _safe_detect_shell_name(original_detector)

    setattr(completion, "_get_shell_name", _patched_detector)
    setattr(completion, "_APIDEV_SHELL_PATCHED", True)


_patch_typer_completion_shell_detection()


app = Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _resolve_cli_version() -> str:
    return __version__


@app.callback(invoke_without_command=True)
def _default_help(
    ctx: Context,
    version: bool = Option(
        False,
        "--version",
        "-v",
        help="Print application version and exit.",
        is_eager=True,
    ),
) -> None:
    if version:
        echo(_resolve_cli_version())
        raise Exit(0)

    if ctx.invoked_subcommand is None:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        app_version = _resolve_cli_version()
        console.print(
            Panel.fit(
                f"[bold cyan]apidev[/bold cyan] [blue]v{app_version}[/blue]\n"
                "[dim]Contract-driven API workflow[/dim]",
                border_style="blue",
                padding=(0, 2),
            )
        )
        echo(ctx.get_help())
        raise Exit(0)


app.command(
    "init",
    help="Initialize apidev project directory and integration profile.",
)(init_command)
app.command("validate", help="Validate contracts and rules")(validate_command)
app.command("graph", help="Inspect contract dependency graph")(graph_command)
app.command("diff", help="Preview generated file changes")(diff_command)
app.command("gen", help="Generate code from contracts")(generate_command)
app.command("generate", hidden=True)(generate_command)


@app.command("version", help="Print application version")
def version_command() -> None:
    echo(_resolve_cli_version())


def main() -> None:
    try:
        app()
    except Exit as e:
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
