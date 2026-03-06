import json
from pathlib import Path

import typer

from apidev.commands.common.option_resolution import unwrap_option_default


def _normalize_flag(value: object) -> bool:
    candidate = unwrap_option_default(value)
    if isinstance(candidate, bool):
        return candidate
    return bool(candidate)


def _normalize_patterns(value: object) -> list[str]:
    candidate = unwrap_option_default(value)
    if candidate is None:
        return []
    if isinstance(candidate, (list, tuple)):
        return [str(item) for item in candidate]
    return [str(candidate)]


def generate_command(
    project_dir: Path = Path("."),
    check: bool = False,
    json_output: bool = typer.Option(False, "--json", help="Print diagnostics as JSON."),
    scaffold: bool = typer.Option(
        False,
        "--scaffold",
        help="Enable scaffold generation for this run.",
    ),
    no_scaffold: bool = typer.Option(
        False,
        "--no-scaffold",
        help="Disable scaffold generation for this run.",
    ),
    compatibility_policy: str | None = typer.Option(
        None,
        "--compatibility-policy",
        help=(
            "Compatibility policy gate for diagnostics: warn or strict. "
            "If omitted, value is taken from .apidev/config.toml."
        ),
        case_sensitive=False,
    ),
    baseline_ref: str | None = typer.Option(
        None,
        "--baseline-ref",
        help="Baseline ref override (git tag or commit), takes precedence over release-state.",
    ),
    include_endpoint: list[str] | None = typer.Option(
        None,
        "--include-endpoint",
        help="Include endpoints matching a case-sensitive glob (repeatable).",
    ),
    exclude_endpoint: list[str] | None = typer.Option(
        None,
        "--exclude-endpoint",
        help="Exclude endpoints matching a case-sensitive glob (repeatable).",
    ),
) -> None:
    from rich.console import Console

    from apidev.application.dto.diagnostics import (
        build_envelope,
        serialize_validation_diagnostic,
    )
    from apidev.application.dto.generation_plan import EndpointFilters
    from apidev.application.services.generate_service import GenerateService
    from apidev.application.services.validate_service import ValidateService
    from apidev.commands.common.baseline_ref import resolve_baseline_ref
    from apidev.commands.common.compatibility import (
        build_compatibility_payload,
        compatibility_diagnostics_unified,
        parse_compatibility_policy,
        print_compatibility,
        resolve_compatibility_policy,
    )
    from apidev.commands.runtime import load_runtime
    from apidev.infrastructure.config.toml_loader import TomlConfigLoader
    from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
    from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
    from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
    from apidev.infrastructure.output.writer import SafeWriter
    from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

    console = Console()

    scaffold_enabled = _normalize_flag(scaffold)
    no_scaffold_enabled = _normalize_flag(no_scaffold)
    if scaffold_enabled and no_scaffold_enabled:
        raise typer.BadParameter("Options --scaffold and --no-scaffold are mutually exclusive.")
    compatibility_policy = parse_compatibility_policy(compatibility_policy)

    root = project_dir.resolve()
    resolved_baseline_ref = resolve_baseline_ref(baseline_ref)
    _, paths = load_runtime(root)
    fs = LocalFileSystem()
    config_loader = TomlConfigLoader(fs=fs)
    config = config_loader.load(root)
    resolved_policy = resolve_compatibility_policy(
        cli_policy=compatibility_policy,
        config_policy=config.evolution.compatibility_policy,
    )
    scaffold_override: bool | None = None
    if scaffold_enabled:
        scaffold_override = True
    elif no_scaffold_enabled:
        scaffold_override = False

    contract_loader = YamlContractLoader()
    validation = ValidateService(
        loader=contract_loader,
        config_loader=config_loader,
    ).run(root)
    if validation.has_errors:
        if json_output:
            payload = build_envelope(
                command="gen",
                mode="check" if check else "apply",
                drift_status="error",
                diagnostics=[
                    serialize_validation_diagnostic(diagnostic, source="validate-service")
                    for diagnostic in validation.diagnostics
                ],
                compatibility=build_compatibility_payload(
                    policy=resolved_policy,
                    compatibility={},
                    source="generate-service",
                ),
            )
            typer.echo(json.dumps(payload, ensure_ascii=False))
            raise SystemExit(1)
        console.print("Validation failed. Run `apidev validate` for details.")
        raise SystemExit(1)

    service = GenerateService(
        config_loader=config_loader,
        loader=contract_loader,
        renderer=JinjaTemplateRenderer(custom_templates_dir=paths.templates_dir),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )
    result = service.run(
        root,
        check=check,
        compatibility_policy=resolved_policy,
        baseline_ref=resolved_baseline_ref,
        scaffold=scaffold_override,
        endpoint_filters=EndpointFilters.from_cli(
            include=_normalize_patterns(include_endpoint),
            exclude=_normalize_patterns(exclude_endpoint),
        ),
    )

    if json_output:
        diagnostics: list[dict[str, object]] = compatibility_diagnostics_unified(
            compatibility=result.compatibility,
            source="generate-service",
        )
        diagnostics.extend([diagnostic.as_unified_dict() for diagnostic in result.diagnostics])
        if result.drift_status == "drift":
            diagnostics.append(
                {
                    "code": "generation.drift-detected",
                    "severity": "error" if check else "warning",
                    "location": "generated-root",
                    "message": (
                        "Drift detected in check mode."
                        if check
                        else "Drift detected during generation."
                    ),
                    "category": "generation",
                    "source": "generate-service",
                    "detail": f"check={str(check).lower()}",
                }
            )
        if check and result.policy_blocked:
            diagnostics.append(
                {
                    "code": "compatibility.policy-blocked",
                    "severity": "error",
                    "location": "compatibility-policy",
                    "message": "Compatibility policy gate failed.",
                    "category": "compatibility",
                    "source": "generate-service",
                    "detail": (
                        f"policy={result.compatibility_policy},"
                        f"overall={result.compatibility.overall}"
                    ),
                }
            )
        compatibility_payload = build_compatibility_payload(
            policy=result.compatibility_policy,
            compatibility=result.compatibility,
            source="generate-service",
        )
        payload = build_envelope(
            command="gen",
            mode="check" if check else "apply",
            drift_status=result.drift_status,
            diagnostics=diagnostics,
            compatibility=compatibility_payload,
            summary_extras={"applied_changes": result.applied_changes},
        )
        typer.echo(json.dumps(payload, ensure_ascii=False))

        should_fail_on_policy = check and result.policy_blocked
        if should_fail_on_policy:
            raise SystemExit(1)
        if result.drift_status == "drift":
            raise SystemExit(1)
        if result.drift_status == "error":
            raise SystemExit(1)
        return

    print_compatibility(console, result.compatibility_policy, result.compatibility)

    should_fail_on_policy = check and result.policy_blocked
    if should_fail_on_policy:
        console.print("Compatibility policy gate failed")
        raise SystemExit(1)

    if result.drift_status == "drift":
        console.print("Drift detected (drift-status: drift)")
        raise SystemExit(1)

    if result.drift_status == "error":
        for diagnostic in result.diagnostics:
            detail_suffix = f" ({diagnostic.detail})" if diagnostic.detail else ""
            console.print(f"\\[{diagnostic.code}] {diagnostic.location}{detail_suffix}")
        console.print("Generation failed (drift-status: error)")
        raise SystemExit(1)

    if check:
        console.print("No drift (drift-status: no-drift)")
        return

    console.print(f"Applied changes: {result.applied_changes} (drift-status: no-drift)")
