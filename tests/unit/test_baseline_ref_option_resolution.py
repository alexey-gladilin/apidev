import pytest
import typer
from typer.models import OptionInfo

from apidev.commands.common.baseline_ref import resolve_baseline_ref


@pytest.mark.parametrize(
    ("resolver",),
    [
        (resolve_baseline_ref,),
    ],
)
def test_resolve_baseline_ref_option_info_default_none_returns_none(resolver) -> None:
    option: OptionInfo = typer.Option(
        None,
        "--baseline-ref",
        help="Baseline ref override (git tag or commit).",
    )

    assert resolver(option) is None


@pytest.mark.parametrize(
    ("resolver",),
    [
        (resolve_baseline_ref,),
    ],
)
def test_resolve_baseline_ref_valid_string_passes_validation(resolver) -> None:
    assert resolver("v2.5.0") == "v2.5.0"


@pytest.mark.parametrize(
    ("resolver",),
    [
        (resolve_baseline_ref,),
    ],
)
def test_resolve_baseline_ref_invalid_string_raises_bad_parameter(resolver) -> None:
    with pytest.raises(typer.BadParameter):
        _ = resolver("bad ref")
