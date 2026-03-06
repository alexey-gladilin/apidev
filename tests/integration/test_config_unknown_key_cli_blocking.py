from pathlib import Path

import pytest
from typer.testing import CliRunner

from apidev.cli import app
from apidev.testing.config_helpers import INIT_INVALID_MANAGED_FILES_MESSAGE, write_config

CONFIG_ERROR_PREFIX = "Invalid configuration in"
KEY_PATH_PREFIX = "key_path="
UNKNOWN_SECTION_PATH = "unknown_section"
UNKNOWN_KEY_PATH = "generator.unknown_key"
CONFIG_ERROR_SUBSTRINGS = {
    "unknown_section": f"{KEY_PATH_PREFIX}{UNKNOWN_SECTION_PATH}",
    "unknown_key": f"{KEY_PATH_PREFIX}{UNKNOWN_KEY_PATH}",
}
FAIL_FAST_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("validate",),
    ("diff", "--json"),
    ("gen", "--check", "--json"),
)

runner = CliRunner()


@pytest.mark.parametrize(
    ("config_text", "expected_key_path"),
    [
        (
            """
[unknown_section]
enabled = true
""",
            CONFIG_ERROR_SUBSTRINGS["unknown_section"],
        ),
        (
            """
[generator]
unknown_key = true
""",
            CONFIG_ERROR_SUBSTRINGS["unknown_key"],
        ),
    ],
)
@pytest.mark.parametrize("command", FAIL_FAST_COMMANDS)
def test_commands_fail_fast_on_unknown_config_entries(
    tmp_path: Path,
    config_text: str,
    expected_key_path: str,
    command: tuple[str, ...],
) -> None:
    write_config(tmp_path, config_text)

    result = runner.invoke(app, [*command, "--project-dir", str(tmp_path)])

    assert result.exit_code != 0
    assert result.exception is not None
    message = str(result.exception)
    assert CONFIG_ERROR_PREFIX in message
    assert expected_key_path in message


def test_init_create_is_blocked_when_config_contains_unknown_key(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[generator]
unknown_key = true
""",
    )

    result = runner.invoke(app, ["init", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert INIT_INVALID_MANAGED_FILES_MESSAGE in result.output


def test_init_create_is_blocked_when_config_contains_unknown_section(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        """
[unknown_section]
enabled = true
""",
    )

    result = runner.invoke(app, ["init", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert INIT_INVALID_MANAGED_FILES_MESSAGE in result.output
