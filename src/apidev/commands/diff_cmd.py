from pathlib import Path

import typer
from rich.console import Console

from apidev.application.services.diff_service import DiffService
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
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

console = Console()


def diff_command(
    project_dir: Path = Path("."),
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
    contract_loader = YamlContractLoader()
    validation = ValidateService(
        loader=contract_loader,
        config_loader=config_loader,
    ).run(root)
    if validation.has_errors:
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
    )
    changed = [
        change for change in plan.changes if change.change_type in {"ADD", "UPDATE", "REMOVE"}
    ]

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
