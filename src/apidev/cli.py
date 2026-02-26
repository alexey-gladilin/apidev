from typer import Typer

from apidev.commands.diff_cmd import diff_command
from apidev.commands.generate_cmd import generate_command
from apidev.commands.init_cmd import init_command
from apidev.commands.validate_cmd import validate_command

app = Typer(
    help="apidev contract-driven API generator",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.command("init", help="Initialize apidev project directory")(init_command)
app.command("validate", help="Validate contracts and rules")(validate_command)
app.command("diff", help="Preview generated file changes")(diff_command)
app.command("gen", help="Generate code from contracts")(generate_command)
app.command("generate", hidden=True)(generate_command)


def main() -> None:
    app()
