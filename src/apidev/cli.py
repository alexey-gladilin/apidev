import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

from typer import Context, Exit, Typer, echo

from apidev.commands.diff_cmd import diff_command
from apidev.commands.generate_cmd import generate_command
from apidev.commands.init_cmd import init_command
from apidev.commands.validate_cmd import validate_command

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
def _default_help(ctx: Context) -> None:
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


app.command("init", help="Initialize apidev project directory")(init_command)
app.command("validate", help="Validate contracts and rules")(validate_command)
app.command("diff", help="Preview generated file changes")(diff_command)
app.command("gen", help="Generate code from contracts")(generate_command)
app.command("generate", hidden=True)(generate_command)


def main() -> None:
    try:
        app()
    except Exit as e:
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
