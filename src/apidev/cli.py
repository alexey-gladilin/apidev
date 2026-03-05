import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import os
from typing import Callable

from typer import Context, Exit, Option, Typer, echo

from apidev.commands.diff_cmd import diff_command
from apidev.commands.generate_cmd import generate_command
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

    original_detector = completion._get_shell_name

    def _patched_detector() -> str | None:
        return _safe_detect_shell_name(original_detector)

    completion._get_shell_name = _patched_detector
    completion._APIDEV_SHELL_PATCHED = True


_patch_typer_completion_shell_detection()


app = Typer(
    help="apidev contract-driven API generator",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _resolve_cli_version() -> str:
    # In local repo runs, prefer pyproject version so changes are visible immediately.
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject_path.exists():
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            project = payload.get("project")
            if isinstance(project, dict):
                pyproject_version = project.get("version")
                if isinstance(pyproject_version, str) and pyproject_version.strip():
                    return pyproject_version.strip()
        except Exception:
            pass

    try:
        return package_version("apidev")
    except PackageNotFoundError:
        from apidev import __version__

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
