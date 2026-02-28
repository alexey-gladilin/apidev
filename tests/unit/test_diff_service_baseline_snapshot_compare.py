from pathlib import Path

import pytest

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project_config(project_dir: Path) -> None:
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
""".strip(),
        encoding="utf-8",
    )


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


def _write_contract(project_dir: Path, relpath: str, body: str) -> None:
    target = project_dir / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _write_release_state(project_dir: Path, baseline_ref: str) -> None:
    (project_dir / ".apidev" / "release-state.json").write_text(
        f'{{"release_number": 2, "baseline_ref": "{baseline_ref}"}}',
        encoding="utf-8",
    )


def _write_corrupted_baseline_cache(project_dir: Path, baseline_ref: str) -> None:
    safe_ref = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in baseline_ref)
    cache_path = project_dir / ".apidev" / "cache" / "baseline" / f"{safe_ref}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Simulate interrupted/invalid cache write.
    cache_path.write_text('{"operations":', encoding="utf-8")


def _create_diff_service() -> DiffService:
    fs = LocalFileSystem()
    return DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )


def test_diff_service_reports_baseline_missing_and_skips_breaking_classification(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
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
""",
    )

    plan = _create_diff_service().run(tmp_path, compatibility_policy="strict")
    codes = [item.code for item in plan.compatibility.diagnostics]

    assert "baseline-missing" in codes
    assert "operation-added" not in codes
    assert "response-field-type-changed" not in codes
    assert "operation-removed" not in codes
    assert plan.policy_blocked is True


def test_diff_service_reports_baseline_invalid_for_unreadable_vcs_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
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
""",
    )
    _write_release_state(tmp_path, baseline_ref="v1.0.0")

    service = _create_diff_service()

    def _fake_git_command(project_dir: Path, args: tuple[str, ...]) -> str | None:
        if args[0] == "ls-tree":
            return ".apidev/contracts/billing/get_invoice.yaml\n"
        if args[0] == "show":
            return ":\n"
        return None

    monkeypatch.setattr(service, "_run_git_command", _fake_git_command)
    plan = service.run(tmp_path, compatibility_policy="strict")
    codes = [item.code for item in plan.compatibility.diagnostics]

    assert "baseline-invalid" in codes
    assert "operation-added" not in codes
    assert plan.policy_blocked is True


def test_diff_service_uses_vcs_when_cache_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
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
""",
    )
    _write_release_state(tmp_path, baseline_ref="v1.0.0")

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
  status: 200
  body:
    type: object
errors: []
"""
        return None

    monkeypatch.setattr(service, "_run_git_command", _fake_git_command)
    plan = service.run(tmp_path, compatibility_policy="strict")
    diagnostics = plan.compatibility.diagnostics
    codes = [item.code for item in diagnostics]
    baseline_applied = [item for item in diagnostics if item.code == "baseline-ref-applied"]

    assert "baseline-missing" not in codes
    assert "baseline-invalid" not in codes
    assert baseline_applied
    assert "snapshot_source=vcs" in baseline_applied[0].detail


def test_diff_service_falls_back_to_vcs_when_cache_json_corrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
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
""",
    )
    baseline_ref = "v1.0.0"
    _write_release_state(tmp_path, baseline_ref=baseline_ref)
    _write_corrupted_baseline_cache(tmp_path, baseline_ref=baseline_ref)

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
  status: 200
  body:
    type: object
errors: []
"""
        return None

    monkeypatch.setattr(service, "_run_git_command", _fake_git_command)
    plan = service.run(tmp_path, compatibility_policy="strict")
    diagnostics = plan.compatibility.diagnostics
    codes = [item.code for item in diagnostics]
    baseline_applied = [item for item in diagnostics if item.code == "baseline-ref-applied"]

    assert "baseline-missing" not in codes
    assert "baseline-invalid" not in codes
    assert baseline_applied
    assert "snapshot_source=vcs" in baseline_applied[0].detail


def _write_oversized_baseline_cache(
    project_dir: Path, baseline_ref: str, max_size_bytes: int = 5_000_000
) -> None:
    """Write baseline cache file exceeding given size limit."""
    safe_ref = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in baseline_ref)
    cache_path = project_dir / ".apidev" / "cache" / "baseline" / f"{safe_ref}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    padding = "x" * (max_size_bytes + 1024 - 80)
    cache_path.write_text(
        f'{{"operations":{{"billing_get_invoice":"fake"}},"padding":"{padding}"}}',
        encoding="utf-8",
    )


def test_diff_service_falls_back_to_vcs_when_baseline_cache_oversized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Oversized baseline cache (>5MB) is ignored; service falls back to VCS."""
    _write_project_config_with_evolution(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
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
""",
    )
    baseline_ref = "v1.0.0"
    _write_release_state(tmp_path, baseline_ref=baseline_ref)
    # Use small limit (100 bytes) so test runs fast; write cache > 100 bytes.
    monkeypatch.setattr(DiffService, "_MAX_BASELINE_CACHE_SIZE_BYTES", 100, raising=False)
    _write_oversized_baseline_cache(tmp_path, baseline_ref=baseline_ref, max_size_bytes=100)

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
  status: 200
  body:
    type: object
errors: []
"""
        return None

    monkeypatch.setattr(service, "_run_git_command", _fake_git_command)
    plan = service.run(tmp_path, compatibility_policy="strict")
    diagnostics = plan.compatibility.diagnostics
    codes = [item.code for item in diagnostics]
    baseline_applied = [item for item in diagnostics if item.code == "baseline-ref-applied"]

    assert "baseline-missing" not in codes
    assert "baseline-invalid" not in codes
    assert baseline_applied
    assert "snapshot_source=vcs" in baseline_applied[0].detail
