from pathlib import Path

import typer
from rich.console import Console

from apidev.application.services.generate_service import GenerateService
from apidev.application.services.validate_service import ValidateService
from apidev.commands.common.baseline_ref import parse_baseline_ref, resolve_baseline_ref
from apidev.commands.common.compatibility import (
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


def _normalize_flag(value: object) -> bool:
    candidate = value
    for _ in range(64):
        if isinstance(candidate, bool):
            return candidate
        default = getattr(candidate, "default", None)
        if default is candidate:
            break
        if default is not None or hasattr(candidate, "default"):
            candidate = default
            continue
        break
    return bool(candidate)


def generate_command(
    project_dir: Path = Path("."),
    check: bool = False,
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
        callback=parse_compatibility_policy,
    ),
    baseline_ref: str | None = typer.Option(
        None,
        "--baseline-ref",
        help="Baseline ref override (git tag or commit), takes precedence over release-state.",
        callback=parse_baseline_ref,
    ),
) -> None:
    scaffold_enabled = _normalize_flag(scaffold)
    no_scaffold_enabled = _normalize_flag(no_scaffold)
    if scaffold_enabled and no_scaffold_enabled:
        raise typer.BadParameter("Options --scaffold and --no-scaffold are mutually exclusive.")

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
    )

    print_compatibility(console, result.compatibility_policy, result.compatibility)

    should_fail_on_policy = check and result.policy_blocked
    if should_fail_on_policy:
        console.print("Compatibility policy gate failed")
        raise SystemExit(1)

    if result.drift_status == "drift":
        console.print("Drift detected (drift-status: drift)")
        raise SystemExit(1)

    if result.drift_status == "error":
        console.print("Generation failed (drift-status: error)")
        raise SystemExit(1)

    if check:
        console.print("No drift (drift-status: no-drift)")
        return

    console.print(f"Applied changes: {result.applied_changes} (drift-status: no-drift)")
