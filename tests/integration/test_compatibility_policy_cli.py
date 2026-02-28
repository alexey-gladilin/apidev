import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from apidev.application.services.generate_service import GenerateService
from apidev.cli import app
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.output.writer import SafeWriter
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

runner = CliRunner()


def _write_project_config(project_dir: Path) -> None:
    (project_dir / ".apidev" / "contracts" / "billing").mkdir(parents=True)
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


def _write_contract(project_dir: Path, api_path: str) -> Path:
    contract_path = project_dir / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
    contract_path.write_text(
        f"""
method: GET
path: {api_path}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body: {{type: object}}
errors: []
""".strip(),
        encoding="utf-8",
    )
    return contract_path


def _run_generate(project_dir: Path) -> None:
    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=project_dir / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )
    _ = service.run(project_dir)


def _write_project_config_with_evolution(
    project_dir: Path,
    grace_period_releases: int = 2,
    compatibility_policy: str | None = None,
) -> None:
    compatibility_policy_line = ""
    if compatibility_policy is not None:
        compatibility_policy_line = f'compatibility_policy = "{compatibility_policy}"\n'

    (project_dir / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        f"""
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"

[evolution]
{compatibility_policy_line}grace_period_releases = {grace_period_releases}
release_state_file = ".apidev/release-state.json"
""".strip(),
        encoding="utf-8",
    )


def _write_release_state(
    project_dir: Path,
    release_number: int,
    baseline_ref: str = "v1.0.0",
    deprecated_operations: dict[str, int] | None = None,
) -> None:
    payload = {
        "release_number": release_number,
        "baseline_ref": baseline_ref,
    }
    if deprecated_operations:
        payload["deprecated_operations"] = deprecated_operations
    (project_dir / ".apidev" / "release-state.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def _write_baseline_cache(
    project_dir: Path, baseline_ref: str, operations: dict[str, str]
) -> None:
    cache_name = "".join(
        ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in baseline_ref
    )
    cache_path = project_dir / ".apidev" / "cache" / "baseline" / f"{cache_name}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "baseline_ref": baseline_ref,
                "operations": operations,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def _git(project_dir: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=project_dir,
        check=True,
        text=True,
        capture_output=True,
    )


def test_diff_warn_policy_is_default_and_reports_compatibility_diagnostics(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    result = runner.invoke(app, ["diff", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "Drift status: drift" in result.output
    assert "Compatibility policy: warn" in result.output
    assert "Compatibility overall:" in result.output
    assert "COMPATIBILITY_" in result.output


def test_diff_strict_policy_fails_on_breaking_compatibility(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    result = runner.invoke(
        app,
        ["diff", "--project-dir", str(tmp_path), "--compatibility-policy", "strict"],
    )

    assert result.exit_code == 1
    assert "Compatibility policy gate failed" in result.output


def test_diff_uses_config_compatibility_policy_when_cli_omitted(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, compatibility_policy="strict")
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(app, ["diff", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert "Compatibility policy: strict" in result.output
    assert "Compatibility policy gate failed" in result.output


def test_diff_cli_compatibility_policy_overrides_config_value(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, compatibility_policy="strict")
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        [
            "diff",
            "--project-dir",
            str(tmp_path),
            "--compatibility-policy",
            "warn",
        ],
    )

    assert result.exit_code == 0
    assert "Compatibility policy: warn" in result.output
    assert "Compatibility policy gate failed" not in result.output


def test_gen_check_uses_config_compatibility_policy_when_cli_omitted(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, compatibility_policy="strict")
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(app, ["gen", "--project-dir", str(tmp_path), "--check"])

    assert result.exit_code == 1
    assert "Compatibility policy: strict" in result.output
    assert "Compatibility policy gate failed" in result.output


def test_gen_check_cli_compatibility_policy_overrides_config_value(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, compatibility_policy="strict")
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--check",
            "--compatibility-policy",
            "warn",
        ],
    )

    assert result.exit_code == 1
    assert "Compatibility policy: warn" in result.output
    assert "Compatibility policy gate failed" not in result.output
    assert "Drift detected (drift-status: drift)" in result.output


def test_gen_check_warn_policy_keeps_existing_drift_exit_semantics(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    result = runner.invoke(app, ["gen", "--project-dir", str(tmp_path), "--check"])

    assert result.exit_code == 1
    assert "Drift detected (drift-status: drift)" in result.output
    assert "Compatibility policy: warn" in result.output


def test_gen_check_strict_policy_reports_policy_failure(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--check",
            "--compatibility-policy",
            "strict",
        ],
    )

    assert result.exit_code == 1
    assert "Compatibility policy gate failed" in result.output


def test_gen_apply_strict_policy_succeeds_after_writes(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--compatibility-policy",
            "strict",
        ],
    )

    assert result.exit_code == 0
    assert "Applied changes:" in result.output


def test_diff_rejects_invalid_compatibility_policy_value(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        [
            "diff",
            "--project-dir",
            str(tmp_path),
            "--compatibility-policy",
            "permissive",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid compatibility policy" in result.output
    assert "warn, strict" in result.output


def test_gen_rejects_invalid_compatibility_policy_value(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--check",
            "--compatibility-policy",
            "permissive",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid compatibility policy" in result.output
    assert "warn, strict" in result.output


def test_diff_strict_flags_deprecation_window_violation_for_early_removal(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    contract_path = _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(
        tmp_path,
        release_number=3,
        deprecated_operations={"billing_get_invoice": 2},
    )
    _write_baseline_cache(tmp_path, "v1.0.0", {"billing_get_invoice": "baseline-fingerprint"})

    contract_path.unlink()
    result = runner.invoke(
        app,
        ["diff", "--project-dir", str(tmp_path), "--compatibility-policy", "strict"],
    )

    assert result.exit_code == 1
    assert "deprecation-window-violation" in result.output
    assert "Compatibility policy gate failed" in result.output


def test_diff_strict_allows_removal_after_deprecation_window(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    contract_path = _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(
        tmp_path,
        release_number=4,
        deprecated_operations={"billing_get_invoice": 2},
    )
    _write_baseline_cache(tmp_path, "v1.0.0", {"billing_get_invoice": "baseline-fingerprint"})

    contract_path.unlink()
    result = runner.invoke(
        app,
        ["diff", "--project-dir", str(tmp_path), "--compatibility-policy", "strict"],
    )

    assert result.exit_code == 0
    assert "deprecation-window-satisfied" in result.output
    assert "Compatibility policy gate failed" not in result.output


def test_diff_and_gen_check_keep_release_state_read_only(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2})
    _run_generate(tmp_path)

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    before_text = release_state_path.read_text(encoding="utf-8")
    before_mtime = release_state_path.stat().st_mtime_ns

    diff_result = runner.invoke(app, ["diff", "--project-dir", str(tmp_path)])
    check_result = runner.invoke(app, ["gen", "--project-dir", str(tmp_path), "--check"])

    assert diff_result.exit_code == 0
    assert check_result.exit_code == 0
    assert release_state_path.read_text(encoding="utf-8") == before_text
    assert release_state_path.stat().st_mtime_ns == before_mtime


def test_diff_baseline_ref_cli_override_has_priority_over_release_state(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2})

    result = runner.invoke(
        app,
        [
            "diff",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "v2.5.0",
        ],
    )

    assert result.exit_code == 0
    assert "baseline-ref-applied" in result.output
    assert "source=cli,baseline_ref=v2.5.0" in result.output


def test_gen_check_baseline_ref_cli_override_has_priority_over_release_state(
    tmp_path: Path,
) -> None:
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2})
    _run_generate(tmp_path)

    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--check",
            "--baseline-ref",
            "release/2026.02",
        ],
    )

    assert result.exit_code == 0
    assert "baseline-ref-applied" in result.output
    assert "source=cli,baseline_ref=release/2026.02" in result.output


def test_diff_rejects_invalid_baseline_ref_override(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        [
            "diff",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "bad ref",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid baseline ref" in result.output


def test_gen_apply_baseline_ref_cli_override_applied(tmp_path: Path) -> None:
    """gen (without --check) with --baseline-ref confirms CLI override application."""
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2})

    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "v2.5.0",
        ],
    )

    assert result.exit_code == 0
    assert "baseline-ref-applied" in result.output
    assert "source=cli,baseline_ref=v2.5.0" in result.output


def test_gen_rejects_invalid_baseline_ref_override(tmp_path: Path) -> None:
    """gen rejects invalid --baseline-ref (analogous to diff)."""
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "bad ref",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid baseline ref" in result.output


def test_diff_strict_fails_with_baseline_missing_diagnostic(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        ["diff", "--project-dir", str(tmp_path), "--compatibility-policy", "strict"],
    )

    assert result.exit_code == 1
    assert "baseline-missing" in result.output
    assert "Compatibility policy gate failed" in result.output


def test_diff_strict_reports_baseline_invalid_from_real_git_baseline(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _git(tmp_path, "config", "user.name", "Tests")

    # Baseline tag stores corrupted contract YAML.
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
        ":\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "corrupt-baseline")
    _git(tmp_path, "tag", "v1.0.0")

    # Current workspace remains valid.
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "restore-valid-contract")

    result = runner.invoke(
        app,
        [
            "diff",
            "--project-dir",
            str(tmp_path),
                "--compatibility-policy",
                "strict",
                "--baseline-ref",
                "v1.0.0",
            ],
        )

    assert result.exit_code == 1
    assert "baseline-invalid" in result.output
    assert "Compatibility policy gate failed" in result.output
