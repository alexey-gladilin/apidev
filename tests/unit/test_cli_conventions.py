from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _read_cli_contract() -> str:
    return (Path("docs/reference/cli-contract.md")).read_text(encoding="utf-8")


def test_no_args_shows_help_by_default() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Commands" in result.output


def test_root_help_supports_short_flag() -> None:
    result = runner.invoke(app, ["-h"])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Commands" in result.output


def test_subcommand_help_supports_short_flag() -> None:
    result = runner.invoke(app, ["init", "-h"])

    assert result.exit_code == 0
    assert "--project-dir" in result.output


def test_gen_command_available_with_short_help() -> None:
    result = runner.invoke(app, ["gen", "-h"])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "gen [OPTIONS]" in result.output


def test_init_rejects_repair_and_force_together() -> None:
    result = runner.invoke(app, ["init", "--repair", "--force"])

    assert result.exit_code == 2
    assert "Use either --repair or --force, not both." in result.output


def test_cli_contract_documents_remove_only_exit_semantics() -> None:
    contract = _read_cli_contract()

    expected_phrases = [
        "`remove-only` изменения считаются `drift`",
        "для `apidev diff` это informational drift с exit `0`",
        "для `apidev gen --check` это blocking drift с exit `1`",
    ]

    for phrase in expected_phrases:
        assert phrase in contract
