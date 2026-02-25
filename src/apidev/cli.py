from typer import Typer

from apidev.commands.diff_cmd import diff_command
from apidev.commands.generate_cmd import generate_command
from apidev.commands.init_cmd import init_command
from apidev.commands.validate_cmd import validate_command

app = Typer(help="apidev contract-driven API generator")
app.command("init")(init_command)
app.command("validate")(validate_command)
app.command("diff")(diff_command)
app.command("generate")(generate_command)


def main() -> None:
    app()
