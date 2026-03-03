from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app
from apidev.application.dto.diagnostics import ValidationResult
from apidev.application.dto.generation_plan import (
    CompatibilityDiagnostic,
    CompatibilitySummary,
    EndpointFilters,
    GenerateResult,
    GenerationDiagnostic,
    GenerationPlan,
    PlannedChange,
)
from apidev.core.models.diagnostic import ValidationDiagnostic
from apidev.core.models.operation import Operation
from apidev.core.models.contract import EndpointContract
from apidev.application.services.validate_service import ValidateService
from apidev.application.services.diff_service import DiffService
from apidev.application.services.generate_service import GenerateService

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


def test_cli_contract_documents_preflight_json_failure_envelopes() -> None:
    contract = _read_cli_contract()

    expected_phrases = [
        "preflight validation failure",
        "`diff --json` и `gen --json`/`gen --check --json`",
        "`drift_status = error`",
    ]

    for phrase in expected_phrases:
        assert phrase in contract


def test_cli_contract_documents_compatibility_diagnostics_in_top_level_for_diff_and_gen() -> None:
    contract = _read_cli_contract()

    expected_phrases = [
        "compatibility diagnostics дублируются",
        "top-level `diagnostics`",
        "`compatibility.diagnostics`",
    ]

    for phrase in expected_phrases:
        assert phrase in contract


def test_validate_json_uses_unified_envelope_and_namespaced_codes(monkeypatch) -> None:
    def _fake_run(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(
            operations=[
                Operation(
                    operation_id="health_check",
                    contract=EndpointContract(
                        source_path=Path("system/health.yaml"),
                        method="GET",
                        path="/v1/health",
                        auth="public",
                        summary="Health",
                        description="Health endpoint",
                        response_status=200,
                        response_body={"type": "object"},
                        errors=[],
                    ),
                    contract_relpath=Path("system/health.yaml"),
                )
            ],
            diagnostics=[
                ValidationDiagnostic(
                    code="SCHEMA_INVALID_VALUE",
                    severity="error",
                    message="Field 'path' must start with '/'.",
                    location="system/health.yaml:path",
                    rule="schema.contract.field_value",
                )
            ],
        )

    monkeypatch.setattr(ValidateService, "run", _fake_run)

    result = runner.invoke(app, ["validate", "--json"])

    assert result.exit_code == 1
    payload = __import__("json").loads(result.output)
    assert payload["command"] == "validate"
    assert payload["mode"] == "validate"
    assert payload["summary"]["diagnostics_total"] == 1
    assert payload["diagnostics"][0]["code"] == "validation.schema-invalid-value"
    assert payload["diagnostics"][0]["category"] == "validation"
    assert payload["diagnostics"][0]["source"] == "validate-service"


def test_diff_json_mode_returns_unified_envelope(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(operations=[], diagnostics=[])

    def _fake_diff(
        self, project_dir: Path, compatibility_policy="warn", baseline_ref=None, scaffold=None
    ) -> GenerationPlan:
        return GenerationPlan(
            generated_root=project_dir / ".apidev" / "output" / "api",
            compatibility_policy="warn",
            compatibility=CompatibilitySummary(
                overall="breaking",
                diagnostics=[
                    CompatibilityDiagnostic(
                        category="breaking",
                        code="compatibility.operation-removed",
                        location="operation:billing_get_invoice",
                        detail="removed-vs-baseline",
                    )
                ],
            ),
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)
    monkeypatch.setattr(DiffService, "run", _fake_diff)

    result = runner.invoke(app, ["diff", "--json"])

    assert result.exit_code == 0
    payload = __import__("json").loads(result.output)
    assert payload["command"] == "diff"
    assert payload["mode"] == "preview"
    assert payload["drift_status"] == "no-drift"
    assert payload["compatibility"]["diagnostics"][0]["code"] == "compatibility.operation-removed"
    assert payload["diagnostics"][0]["code"] == "compatibility.operation-removed"


def test_diff_json_drift_exit_semantics_keep_preview_non_blocking(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(operations=[], diagnostics=[])

    def _fake_diff(
        self, project_dir: Path, compatibility_policy="warn", baseline_ref=None, scaffold=None
    ) -> GenerationPlan:
        return GenerationPlan(
            generated_root=project_dir / ".apidev" / "output" / "api",
            changes=[PlannedChange(path=Path("users.py"), content="x", change_type="ADD")],
            compatibility_policy="warn",
            compatibility=CompatibilitySummary(),
            policy_blocked=False,
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)
    monkeypatch.setattr(DiffService, "run", _fake_diff)

    result = runner.invoke(app, ["diff", "--json"])

    assert result.exit_code == 0
    payload = __import__("json").loads(result.output)
    assert payload["command"] == "diff"
    assert payload["mode"] == "preview"
    assert payload["drift_status"] == "drift"
    assert payload["summary"]["status"] == "ok"
    assert payload["diagnostics"][0]["code"] == "generation.drift-detected"


def test_gen_check_json_mode_returns_unified_envelope(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(operations=[], diagnostics=[])

    def _fake_generate(
        self,
        project_dir: Path,
        check: bool = False,
        compatibility_policy="warn",
        baseline_ref=None,
        scaffold=None,
        endpoint_filters=None,
    ) -> GenerateResult:
        assert check is True
        return GenerateResult(
            applied_changes=0,
            drift_status="drift",
            diagnostics=[],
            compatibility_policy="warn",
            compatibility=CompatibilitySummary(),
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)
    monkeypatch.setattr(GenerateService, "run", _fake_generate)

    result = runner.invoke(app, ["gen", "--check", "--json"])

    assert result.exit_code == 1
    payload = __import__("json").loads(result.output)
    assert payload["command"] == "gen"
    assert payload["mode"] == "check"
    assert payload["drift_status"] == "drift"
    assert payload["summary"]["status"] == "failed"
    assert payload["diagnostics"][0]["code"] == "generation.drift-detected"


def test_gen_apply_json_merges_compatibility_and_generation_taxonomy(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(operations=[], diagnostics=[])

    def _fake_generate(
        self,
        project_dir: Path,
        check: bool = False,
        compatibility_policy="warn",
        baseline_ref=None,
        scaffold=None,
        endpoint_filters=None,
    ) -> GenerateResult:
        assert check is False
        return GenerateResult(
            applied_changes=0,
            drift_status="drift",
            diagnostics=[],
            compatibility_policy="warn",
            compatibility=CompatibilitySummary(
                overall="potentially-breaking",
                diagnostics=[
                    CompatibilityDiagnostic(
                        category="potentially-breaking",
                        code="compatibility.response-field-required-added",
                        location="operation:billing_get_invoice",
                        detail="field=note",
                    )
                ],
            ),
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)
    monkeypatch.setattr(GenerateService, "run", _fake_generate)

    result = runner.invoke(app, ["gen", "--json"])

    assert result.exit_code == 1
    payload = __import__("json").loads(result.output)
    codes = [item["code"] for item in payload["diagnostics"]]
    assert payload["command"] == "gen"
    assert payload["mode"] == "apply"
    assert payload["drift_status"] == "drift"
    assert "compatibility.response-field-required-added" in codes
    assert "generation.drift-detected" in codes
    assert payload["summary"]["diagnostics_total"] == len(payload["diagnostics"])
    compatibility_sources = {
        item["source"]
        for item in payload["diagnostics"]
        if item["code"].startswith("compatibility.")
    }
    assert compatibility_sources == {"generate-service"}
    assert payload["compatibility"]["diagnostics"][0]["source"] == "generate-service"


def test_diff_json_keeps_compatibility_diagnostics_deterministic_and_in_summary(
    monkeypatch,
) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(operations=[], diagnostics=[])

    def _fake_diff(
        self, project_dir: Path, compatibility_policy="warn", baseline_ref=None, scaffold=None
    ) -> GenerationPlan:
        return GenerationPlan(
            generated_root=project_dir / ".apidev" / "output" / "api",
            compatibility_policy="strict",
            policy_blocked=True,
            compatibility=CompatibilitySummary(
                overall="breaking",
                diagnostics=[
                    CompatibilityDiagnostic(
                        category="breaking",
                        code="compatibility.response-field-type-changed",
                        location="operation:b",
                        detail="b",
                    ),
                    CompatibilityDiagnostic(
                        category="breaking",
                        code="compatibility.baseline-missing",
                        location="baseline",
                        detail="a",
                    ),
                ],
            ),
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)
    monkeypatch.setattr(DiffService, "run", _fake_diff)

    result = runner.invoke(app, ["diff", "--json"])

    assert result.exit_code == 1
    payload = __import__("json").loads(result.output)
    codes = [item["code"] for item in payload["diagnostics"]]
    assert codes == sorted(codes)
    assert "compatibility.baseline-missing" in codes
    assert payload["summary"]["diagnostics_total"] == len(payload["diagnostics"])


def test_diff_json_preflight_validation_failure_returns_unified_envelope(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(
            operations=[],
            diagnostics=[
                ValidationDiagnostic(
                    code="SCHEMA_INVALID_VALUE",
                    severity="error",
                    message="Broken contract",
                    location="contracts/broken.yaml:path",
                    rule="schema.contract.field_value",
                )
            ],
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)

    result = runner.invoke(app, ["diff", "--json"])

    assert result.exit_code == 1
    payload = __import__("json").loads(result.output)
    assert payload["command"] == "diff"
    assert payload["mode"] == "preview"
    assert payload["drift_status"] == "error"
    assert payload["summary"]["status"] == "failed"
    assert payload["diagnostics"][0]["code"] == "validation.schema-invalid-value"
    assert payload["compatibility"]["overall"] == "non-breaking"
    assert payload["compatibility"]["diagnostics"] == []


def test_gen_json_preflight_validation_failure_returns_unified_envelope(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(
            operations=[],
            diagnostics=[
                ValidationDiagnostic(
                    code="SCHEMA_INVALID_VALUE",
                    severity="error",
                    message="Broken contract",
                    location="contracts/broken.yaml:path",
                    rule="schema.contract.field_value",
                )
            ],
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)

    result = runner.invoke(app, ["gen", "--json"])

    assert result.exit_code == 1
    payload = __import__("json").loads(result.output)
    assert payload["command"] == "gen"
    assert payload["mode"] == "apply"
    assert payload["drift_status"] == "error"
    assert payload["summary"]["status"] == "failed"
    assert payload["diagnostics"][0]["code"] == "validation.schema-invalid-value"
    assert payload["compatibility"]["overall"] == "non-breaking"
    assert payload["compatibility"]["diagnostics"] == []


def test_gen_check_json_preflight_validation_failure_returns_unified_envelope(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(
            operations=[],
            diagnostics=[
                ValidationDiagnostic(
                    code="SCHEMA_INVALID_VALUE",
                    severity="error",
                    message="Broken contract",
                    location="contracts/broken.yaml:path",
                    rule="schema.contract.field_value",
                )
            ],
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)

    result = runner.invoke(app, ["gen", "--check", "--json"])

    assert result.exit_code == 1
    payload = __import__("json").loads(result.output)
    assert payload["command"] == "gen"
    assert payload["mode"] == "check"
    assert payload["drift_status"] == "error"
    assert payload["summary"]["status"] == "failed"
    assert payload["diagnostics"][0]["code"] == "validation.schema-invalid-value"
    assert payload["compatibility"]["overall"] == "non-breaking"
    assert payload["compatibility"]["diagnostics"] == []


def test_gen_help_documents_endpoint_filter_flags() -> None:
    result = runner.invoke(app, ["gen", "-h"])

    assert result.exit_code == 0
    assert "--include-endpoint" in result.output
    assert "--exclude-endpoint" in result.output


def test_gen_passes_endpoint_filters_to_generate_service(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(operations=[], diagnostics=[])

    captured: dict[str, object] = {}

    def _fake_generate(
        self,
        project_dir: Path,
        check: bool = False,
        compatibility_policy="warn",
        baseline_ref=None,
        scaffold=None,
        endpoint_filters=None,
    ) -> GenerateResult:
        captured["endpoint_filters"] = endpoint_filters
        return GenerateResult(applied_changes=0, drift_status="no-drift")

    monkeypatch.setattr(ValidateService, "run", _fake_validate)
    monkeypatch.setattr(GenerateService, "run", _fake_generate)

    result = runner.invoke(
        app,
        [
            "gen",
            "--include-endpoint",
            " billing_* ",
            "--exclude-endpoint",
            "users_*",
        ],
    )

    assert result.exit_code == 0
    assert captured["endpoint_filters"] == EndpointFilters(
        include=("billing_*",),
        exclude=("users_*",),
    )


def test_gen_text_mode_prints_generation_diagnostics_on_error(monkeypatch) -> None:
    def _fake_validate(self, project_dir: Path) -> ValidationResult:
        return ValidationResult(operations=[], diagnostics=[])

    def _fake_generate(
        self,
        project_dir: Path,
        check: bool = False,
        compatibility_policy="warn",
        baseline_ref=None,
        scaffold=None,
        endpoint_filters=None,
    ) -> GenerateResult:
        return GenerateResult(
            applied_changes=0,
            drift_status="error",
            diagnostics=[
                GenerationDiagnostic(
                    code="generation.invalid-endpoint-pattern",
                    location="include-endpoint[0]",
                    detail="malformed glob pattern",
                )
            ],
        )

    monkeypatch.setattr(ValidateService, "run", _fake_validate)
    monkeypatch.setattr(GenerateService, "run", _fake_generate)

    result = runner.invoke(app, ["gen", "--include-endpoint", "["])

    assert result.exit_code == 1
    assert "[generation.invalid-endpoint-pattern] include-endpoint[0]" in result.output
    assert "malformed glob" in result.output
    assert "pattern" in result.output
