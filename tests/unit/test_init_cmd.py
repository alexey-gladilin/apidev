from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from apidev.application.services.init_service import InitResult
from apidev.cli import app

runner = CliRunner()


def test_init_help_documents_profile_flags_and_enum_contract() -> None:
    result = runner.invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    assert "--runtime" in result.output
    assert "--integration-mode" in result.output
    assert "--integration-dir" in result.output
    assert "[fastapi|none]" in result.output
    assert "[off|scaffold|full]" in result.output


def test_init_accepts_profile_flags_in_canonical_syntax(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class _FakeInitService:
        def __init__(self, fs: object, default_config_text: str):
            captured["created"] = True

        def run(self, project_dir: Path, mode: str = "create", **kwargs: Any) -> InitResult:
            captured["project_dir"] = project_dir
            captured["mode"] = mode
            captured["runtime"] = kwargs.get("runtime")
            captured["integration_mode"] = kwargs.get("integration_mode")
            return InitResult(status="initialized", changed=1)

    monkeypatch.setattr("apidev.application.services.init_service.InitService", _FakeInitService)

    result = runner.invoke(
        app,
        [
            "init",
            "--runtime",
            "fastapi",
            "--integration-mode",
            "scaffold",
            "--integration-dir",
            "integration/http",
        ],
    )

    assert result.exit_code == 0
    assert captured["created"] is True
    assert captured["mode"] == "create"
    assert captured["runtime"] == "fastapi"
    assert captured["integration_mode"] == "scaffold"


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("--runtime", "flask"),
        ("--runtime", ""),
        ("--runtime", "undefined"),
        ("--runtime", "null"),
        ("--integration-mode", "invalid"),
        ("--integration-mode", ""),
        ("--integration-mode", "undefined"),
        ("--integration-mode", "null"),
    ],
)
def test_init_rejects_invalid_profile_enums_before_file_ops(
    flag: str,
    value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"run": False}

    class _FakeInitService:
        def __init__(self, fs: object, default_config_text: str):
            pass

        def run(self, project_dir: Path, mode: str = "create", **kwargs: Any) -> InitResult:
            called["run"] = True
            return InitResult(status="initialized", changed=1)

    monkeypatch.setattr("apidev.application.services.init_service.InitService", _FakeInitService)

    result = runner.invoke(app, ["init", flag, value])

    assert result.exit_code == 2
    assert "config.INIT_PROFILE_INVALID_ENUM" in result.output
    assert called["run"] is False


@pytest.mark.parametrize(
    ("runtime", "integration_mode"),
    [
        ("", "scaffold"),
        ("undefined", "scaffold"),
        ("null", "scaffold"),
        ("fastapi", ""),
        ("fastapi", "undefined"),
        ("fastapi", "null"),
    ],
)
def test_init_rejects_empty_or_null_like_profile_values_in_programmatic_calls(
    runtime: str,
    integration_mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"run": False}

    class _FakeInitService:
        def __init__(self, fs: object, default_config_text: str):
            pass

        def run(self, project_dir: Path, mode: str = "create", **kwargs: Any) -> InitResult:
            called["run"] = True
            return InitResult(status="initialized", changed=1)

    monkeypatch.setattr("apidev.application.services.init_service.InitService", _FakeInitService)

    with pytest.raises(Exception) as exc_info:
        from apidev.commands.init_cmd import init_command

        init_command(
            project_dir=Path("."),
            runtime=runtime,
            integration_mode=integration_mode,
            integration_dir="integration",
        )

    assert "config.INIT_PROFILE_INVALID_ENUM" in str(exc_info.value)
    assert called["run"] is False


def test_init_rejects_runtime_none_with_full_integration_mode_before_file_ops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"run": False}

    class _FakeInitService:
        def __init__(self, fs: object, default_config_text: str):
            pass

        def run(self, project_dir: Path, mode: str = "create", **kwargs: Any) -> InitResult:
            called["run"] = True
            return InitResult(status="initialized", changed=1)

    monkeypatch.setattr("apidev.application.services.init_service.InitService", _FakeInitService)

    result = runner.invoke(
        app,
        ["init", "--runtime", "none", "--integration-mode", "full"],
    )

    assert result.exit_code == 2
    assert "config.INIT_MODE_CONFLICT" in result.output
    assert called["run"] is False


@pytest.mark.parametrize("integration_dir", ["../outside", "/tmp/outside"])
def test_init_rejects_integration_dir_outside_project_boundary(
    integration_dir: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"run": False}

    class _FakeInitService:
        def __init__(self, fs: object, default_config_text: str):
            pass

        def run(self, project_dir: Path, mode: str = "create", **kwargs: Any) -> InitResult:
            called["run"] = True
            return InitResult(status="initialized", changed=1)

    monkeypatch.setattr("apidev.application.services.init_service.InitService", _FakeInitService)

    result = runner.invoke(app, ["init", "--integration-dir", integration_dir])

    assert result.exit_code == 2
    assert "validation.PATH_BOUNDARY_VIOLATION" in result.output
    assert called["run"] is False


def test_init_rejects_none_integration_dir_in_programmatic_calls_before_file_ops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"run": False}

    class _FakeInitService:
        def __init__(self, fs: object, default_config_text: str):
            pass

        def run(self, project_dir: Path, mode: str = "create", **kwargs: Any) -> InitResult:
            called["run"] = True
            return InitResult(status="initialized", changed=1)

    monkeypatch.setattr("apidev.application.services.init_service.InitService", _FakeInitService)

    with pytest.raises(Exception) as exc_info:
        from apidev.commands.init_cmd import init_command

        init_command(
            project_dir=Path("."),
            runtime="fastapi",
            integration_mode="scaffold",
            integration_dir=None,  # type: ignore[arg-type]
        )

    assert "validation.PATH_BOUNDARY_VIOLATION" in str(exc_info.value)
    assert called["run"] is False
