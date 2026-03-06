import json
import re
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
PATH_PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")


def _write_project_config(project_dir: Path) -> None:
    (project_dir / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        """
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[paths]
templates_dir = ".apidev/templates"
""".strip(),
        encoding="utf-8",
    )


def _write_contract(project_dir: Path, api_path: str) -> Path:
    placeholders = sorted(set(PATH_PLACEHOLDER_PATTERN.findall(api_path)))
    request_block = ""
    if placeholders:
        properties = "\n".join(
            f"      {name}:\n        type: string\n        required: true" for name in placeholders
        )
        request_block = (
            "request:\n" "  path:\n" "    type: object\n" "    properties:\n" f"{properties}\n"
        )

    contract_path = project_dir / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
    contract_path.write_text(
        f"""
method: GET
path: {api_path}
auth: bearer
summary: Get invoice
description: Get invoice details
{request_block}\
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
    _ = service.run(project_dir, baseline_ref="v1.0.0")


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
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[paths]
templates_dir = ".apidev/templates"

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


def _write_baseline_cache(project_dir: Path, baseline_ref: str, operations: dict[str, str]) -> None:
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


def test_diff_reports_drift_for_remove_only_changes(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    stale_path = (
        tmp_path / ".apidev" / "output" / "api" / "billing" / "routes" / "obsolete_route.py"
    )
    stale_path.write_text("# stale\n", encoding="utf-8")

    result = runner.invoke(app, ["diff", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "Drift status: drift" in result.output
    assert "REMOVE" in result.output
    assert stale_path.name in result.output.replace("\n", "")


def test_gen_check_fails_on_drift_from_remove_only_changes(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    stale_path = (
        tmp_path / ".apidev" / "output" / "api" / "billing" / "routes" / "obsolete_route.py"
    )
    stale_path.write_text("# stale\n", encoding="utf-8")

    result = runner.invoke(app, ["gen", "--project-dir", str(tmp_path), "--check"])

    assert result.exit_code == 1
    assert "Drift detected (drift-status: drift)" in result.output


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
            "--baseline-ref",
            "v1.0.0",
        ],
    )

    assert result.exit_code == 0
    assert "Applied changes:" in result.output


def test_gen_apply_release_state_lifecycle_auto_create_bump_and_noop(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    first_apply = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "v1.0.0",
        ],
    )
    assert first_apply.exit_code == 0

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    first_payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert first_payload["release_number"] == 1
    assert first_payload["baseline_ref"] == "v1.0.0"

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    second_apply = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "v1.0.0",
        ],
    )
    assert second_apply.exit_code == 0

    second_payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert second_payload["release_number"] == 2
    assert second_payload["baseline_ref"] == "v1.0.0"

    no_op_apply = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "v1.0.0",
        ],
    )
    assert no_op_apply.exit_code == 0

    final_payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert final_payload["release_number"] == 2
    assert final_payload["baseline_ref"] == "v1.0.0"


def test_gen_apply_exits_with_error_when_remove_apply_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    stale_path = (
        tmp_path / ".apidev" / "output" / "api" / "billing" / "routes" / "obsolete_route.py"
    )
    stale_path.write_text("# stale\n", encoding="utf-8")

    def _raise_remove_error(self, generated_dir_path: Path, target: Path) -> bool:
        raise ValueError(f"remove failed for {target}")

    monkeypatch.setattr(GenerateService, "_remove_generated_artifact", _raise_remove_error)

    result = runner.invoke(app, ["gen", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert "Generation failed (drift-status: error)" in result.output


def test_gen_apply_keeps_release_state_pre_run_payload_when_release_state_bump_write_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(tmp_path, release_number=3, baseline_ref="v1.0.0")
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    before_text = release_state_path.read_text(encoding="utf-8")
    original_write_text = LocalFileSystem.write_text

    def _fail_on_bump_write(self, path: Path, content: str) -> None:
        if path == release_state_path and '"release_number": 4' in content:
            raise OSError("simulated release-state write failure")
        original_write_text(self, path, content)

    monkeypatch.setattr(LocalFileSystem, "write_text", _fail_on_bump_write)

    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "v2.0.0",
        ],
    )

    assert result.exit_code == 1
    assert release_state_path.read_text(encoding="utf-8") == before_text


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
    _write_release_state(
        tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2}
    )
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


def test_diff_strict_failure_keeps_release_state_read_only(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, compatibility_policy="strict")
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    before_text = release_state_path.read_text(encoding="utf-8")
    before_mtime = release_state_path.stat().st_mtime_ns

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    result = runner.invoke(app, ["diff", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert "Compatibility policy gate failed" in result.output
    assert release_state_path.read_text(encoding="utf-8") == before_text
    assert release_state_path.stat().st_mtime_ns == before_mtime


def test_gen_check_drift_failure_keeps_release_state_read_only(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    before_text = release_state_path.read_text(encoding="utf-8")
    before_mtime = release_state_path.stat().st_mtime_ns

    _write_contract(tmp_path, "/v1/invoices/{invoice_id}/details")
    result = runner.invoke(app, ["gen", "--project-dir", str(tmp_path), "--check"])

    assert result.exit_code == 1
    assert "Drift detected (drift-status: drift)" in result.output
    assert release_state_path.read_text(encoding="utf-8") == before_text
    assert release_state_path.stat().st_mtime_ns == before_mtime


def test_diff_baseline_ref_cli_override_has_priority_over_release_state(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path, grace_period_releases=2)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    _run_generate(tmp_path)
    _write_release_state(
        tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2}
    )

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
    _write_release_state(
        tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2}
    )
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
    _write_release_state(
        tmp_path, release_number=4, deprecated_operations={"billing_get_invoice": 2}
    )

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


def test_diff_strict_reports_baseline_invalid_for_no_git_with_baseline_ref(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number":2,"baseline_ref":"v1.0.0"}',
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["diff", "--project-dir", str(tmp_path), "--compatibility-policy", "strict"],
    )

    assert result.exit_code == 1
    assert "baseline-invalid" in result.output
    assert "baseline-missing" not in result.output
    assert "Compatibility policy gate failed" in result.output


def test_diff_reports_release_state_invalid_with_baseline_missing(tmp_path: Path) -> None:
    _write_project_config_with_evolution(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")
    (tmp_path / ".apidev" / "release-state.json").write_text(
        '{"release_number":2,"baseline_ref":"bad ref"}',
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["diff", "--project-dir", str(tmp_path), "--compatibility-policy", "strict"],
    )

    assert result.exit_code == 1
    assert "release-state-invalid" in result.output
    assert "baseline-missing" in result.output
    assert "Compatibility policy gate failed" in result.output


def test_diff_json_includes_compatibility_diagnostics_in_unified_envelope(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(tmp_path, "/v1/invoices/{invoice_id}")

    result = runner.invoke(
        app,
        [
            "diff",
            "--project-dir",
            str(tmp_path),
            "--compatibility-policy",
            "strict",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    top_level_codes = [item["code"] for item in payload["diagnostics"]]
    compatibility_codes = [item["code"] for item in payload["compatibility"]["diagnostics"]]

    assert "compatibility.baseline-missing" in compatibility_codes
    assert "compatibility.baseline-missing" in top_level_codes
    assert payload["summary"]["diagnostics_total"] == len(payload["diagnostics"])


def test_gen_check_json_includes_compatibility_diagnostics_in_unified_envelope(
    tmp_path: Path,
) -> None:
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
            "strict",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    top_level_codes = [item["code"] for item in payload["diagnostics"]]
    compatibility_codes = [item["code"] for item in payload["compatibility"]["diagnostics"]]

    assert "compatibility.baseline-missing" in compatibility_codes
    assert "compatibility.baseline-missing" in top_level_codes
    assert payload["summary"]["diagnostics_total"] == len(payload["diagnostics"])
