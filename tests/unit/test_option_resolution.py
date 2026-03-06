import typer

from apidev.commands.common.option_resolution import unwrap_option_default


class _OptionLike:
    def __init__(self, default: object):
        self.default = default


def test_unwrap_option_default_reads_typer_option_default() -> None:
    option = typer.Option(
        "warn",
        "--compatibility-policy",
    )

    assert unwrap_option_default(option, max_depth=8) == "warn"


def test_unwrap_option_default_reads_nested_default_chain() -> None:
    nested = _OptionLike(_OptionLike(True))

    assert unwrap_option_default(nested, max_depth=8) is True
