import json
from pathlib import Path

import typer

from apidev.commands.common.option_resolution import unwrap_option_default


def _normalize_flag(value: object) -> bool:
    candidate = unwrap_option_default(value)
    if isinstance(candidate, bool):
        return candidate
    return bool(candidate)


def diff_command(
    project_dir: Path = Path("."),
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
) -> None:
    from rich.console import Console

    from apidev.application.dto.diagnostics import (
        build_envelope,
        serialize_validation_diagnostic,
    )
    from apidev.application.services.diff_service import DiffService
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
                command="diff",
                mode="preview",
                drift_status="error",
                diagnostics=[
                    serialize_validation_diagnostic(diagnostic, source="validate-service")
                    for diagnostic in validation.diagnostics
                ],
                compatibility=build_compatibility_payload(
                    policy=resolved_policy,
                    compatibility={},
                    source="diff-service",
                ),
            )
            typer.echo(json.dumps(payload, ensure_ascii=False))
            raise SystemExit(1)
        console.print("Validation failed. Run `apidev validate` for details.")
        raise SystemExit(1)

    service = DiffService(
        config_loader=config_loader,
        loader=contract_loader,
        renderer=JinjaTemplateRenderer(custom_templates_dir=paths.templates_dir),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )
    plan = service.run(
        root,
        compatibility_policy=resolved_policy,
        baseline_ref=resolved_baseline_ref,
        scaffold=scaffold_override,
    )
    changed = [
        change for change in plan.changes if change.change_type in {"ADD", "UPDATE", "REMOVE"}
    ]
    drift_status = "drift" if changed else "no-drift"

    if json_output:
        diagnostics: list[dict[str, object]] = compatibility_diagnostics_unified(
            compatibility=plan.compatibility,
            source="diff-service",
        )
        if changed:
            diagnostics.append(
                {
                    "code": "generation.drift-detected",
                    "severity": "info",
                    "location": "generated-root",
                    "message": "Drift detected in preview mode.",
                    "category": "generation",
                    "source": "diff-service",
                    "detail": (
                        "ADD="
                        f"{sum(1 for c in changed if c.change_type == 'ADD')},"
                        f"UPDATE={sum(1 for c in changed if c.change_type == 'UPDATE')},"
                        f"REMOVE={sum(1 for c in changed if c.change_type == 'REMOVE')}"
                    ),
                }
            )
        if plan.policy_blocked:
            diagnostics.append(
                {
                    "code": "compatibility.policy-blocked",
                    "severity": "error",
                    "location": "compatibility-policy",
                    "message": "Compatibility policy gate failed.",
                    "category": "compatibility",
                    "source": "diff-service",
                    "detail": f"policy={plan.compatibility_policy},overall={plan.compatibility.overall}",
                }
            )
        compatibility_payload = build_compatibility_payload(
            policy=plan.compatibility_policy,
            compatibility=plan.compatibility,
            source="diff-service",
        )
        payload = build_envelope(
            command="diff",
            mode="preview",
            drift_status=drift_status,
            diagnostics=diagnostics,
            compatibility=compatibility_payload,
        )
        typer.echo(json.dumps(payload, ensure_ascii=False))
        if plan.policy_blocked:
            raise SystemExit(1)
        return

    if not changed:
        console.print("No changes")
        console.print("Drift status: no-drift")
        print_compatibility(console, plan.compatibility_policy, plan.compatibility)
        if plan.policy_blocked:
            console.print("Compatibility policy gate failed")
            raise SystemExit(1)
        return

    for change in changed:
        console.print(f"{change.change_type:>7} {change.path}")
    print_compatibility(console, plan.compatibility_policy, plan.compatibility)
    console.print("Drift status: drift")
    if plan.policy_blocked:
        console.print("Compatibility policy gate failed")
        raise SystemExit(1)
