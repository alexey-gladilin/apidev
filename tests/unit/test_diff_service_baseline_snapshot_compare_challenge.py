from pathlib import Path

import pytest

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project_config_with_evolution(project_dir: Path) -> None:
    (project_dir / ".apidev" / "contracts").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"

[evolution]
release_state_file = ".apidev/release-state.json"
""".strip(),
        encoding="utf-8",
    )


def _write_contract(project_dir: Path) -> None:
    target = project_dir / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )


def _create_diff_service() -> DiffService:
    fs = LocalFileSystem()
    return DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )


def test_diff_service_handles_null_release_state_baseline_ref_as_invalid(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(tmp_path)
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number":2,"baseline_ref":null}',
        encoding="utf-8",
    )

    plan = _create_diff_service().run(tmp_path, compatibility_policy="strict")
    codes = [item.code for item in plan.compatibility.diagnostics]

    assert "release-state-invalid" in codes
    assert "baseline-missing" in codes
    assert "operation-added" not in codes
    assert plan.policy_blocked is True


def test_diff_service_handles_empty_release_state_baseline_ref_as_invalid(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(tmp_path)
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number":2,"baseline_ref":"   "}',
        encoding="utf-8",
    )

    plan = _create_diff_service().run(tmp_path, compatibility_policy="strict")
    codes = [item.code for item in plan.compatibility.diagnostics]

    assert "release-state-invalid" in codes
    assert "baseline-missing" in codes
    assert "response-field-type-changed" not in codes
    assert plan.policy_blocked is True


def test_diff_service_marks_invalid_baseline_status_type_in_strict_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(tmp_path)
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number":2,"baseline_ref":"v1.0.0"}',
        encoding="utf-8",
    )
    service = _create_diff_service()

    def _fake_git_command(project_dir: Path, args: tuple[str, ...]) -> str | None:
        if args[0] == "ls-tree":
            return ".apidev/contracts/billing/get_invoice.yaml\n"
        if args[0] == "show":
            return """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: nope
  body:
    type: object
errors: []
"""
        return None

    monkeypatch.setattr(service, "_run_git_command", _fake_git_command)

    plan = service.run(tmp_path, compatibility_policy="strict")
    codes = [item.code for item in plan.compatibility.diagnostics]

    assert "baseline-invalid" in codes
    assert "operation-added" not in codes
    assert plan.policy_blocked is True


def test_diff_service_marks_invalid_baseline_status_type_in_warn_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(tmp_path)
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number":2,"baseline_ref":"v1.0.0"}',
        encoding="utf-8",
    )
    service = _create_diff_service()

    def _fake_git_command(project_dir: Path, args: tuple[str, ...]) -> str | None:
        if args[0] == "ls-tree":
            return ".apidev/contracts/billing/get_invoice.yaml\n"
        if args[0] == "show":
            return """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: nope
  body:
    type: object
errors: []
"""
        return None

    monkeypatch.setattr(service, "_run_git_command", _fake_git_command)

    plan = service.run(tmp_path, compatibility_policy="warn")
    codes = [item.code for item in plan.compatibility.diagnostics]

    assert "baseline-invalid" in codes
    assert "operation-added" not in codes
    assert plan.policy_blocked is False
