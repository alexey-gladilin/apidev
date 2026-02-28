from pathlib import Path

import typer
from rich.console import Console

from apidev.application.services.diff_service import DiffService
from apidev.application.services.validate_service import ValidateService
from apidev.commands.common.baseline_ref import parse_baseline_ref, resolve_baseline_ref
from apidev.commands.runtime import load_runtime
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

console = Console()


def _parse_compatibility_policy(policy: str) -> str:
    normalized = str(policy).strip().lower()
    if normalized in {"warn", "strict"}:
        return normalized
    raise typer.BadParameter(
        f"Invalid compatibility policy '{policy}'. Expected one of: warn, strict."
    )


def diff_command(
    project_dir: Path = Path("."),
    compatibility_policy: str = typer.Option(
        "warn",
        "--compatibility-policy",
        help="Compatibility policy gate for diagnostics: warn (default) or strict.",
        case_sensitive=False,
        callback=_parse_compatibility_policy,
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
    contract_loader = YamlContractLoader()
    validation = ValidateService(
        loader=contract_loader,
        config_loader=TomlConfigLoader(fs=fs),
    ).run(root)
    if validation.has_errors:
        console.print("Validation failed. Run `apidev validate` for details.")
        raise SystemExit(1)

    service = DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=contract_loader,
        renderer=JinjaTemplateRenderer(custom_templates_dir=paths.templates_dir),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )
    plan = service.run(
        root,
        compatibility_policy=compatibility_policy,
        baseline_ref=resolved_baseline_ref,
    )
    changed = [change for change in plan.changes if change.change_type in {"ADD", "UPDATE"}]

    if not changed:
        console.print("No changes")
        console.print("Drift status: no-drift")
        _print_compatibility(plan.compatibility_policy, plan.compatibility)
        if plan.policy_blocked:
            console.print("Compatibility policy gate failed")
            raise SystemExit(1)
        return

    for change in changed:
        console.print(f"{change.change_type:>7} {change.path}")
    _print_compatibility(plan.compatibility_policy, plan.compatibility)
    console.print("Drift status: drift")
    if plan.policy_blocked:
        console.print("Compatibility policy gate failed")
        raise SystemExit(1)


def _print_compatibility(policy: str, compatibility: object) -> None:
    overall = str(getattr(compatibility, "overall", "non-breaking"))
    counts = getattr(compatibility, "counts", {})
    diagnostics = getattr(compatibility, "diagnostics", [])

    console.print(f"Compatibility policy: {policy}")
    console.print(
        "Compatibility overall: "
        f"{overall} "
        f"(breaking={counts.get('breaking', 0)}, "
        f"potentially-breaking={counts.get('potentially-breaking', 0)}, "
        f"non-breaking={counts.get('non-breaking', 0)})"
    )

    for diagnostic in diagnostics:
        category = str(getattr(diagnostic, "category", "potentially-breaking")).upper().replace(
            "-", "_"
        )
        code = str(getattr(diagnostic, "code", "unknown"))
        location = str(getattr(diagnostic, "location", "unknown"))
        detail = str(getattr(diagnostic, "detail", ""))
        suffix = f" ({detail})" if detail else ""
        console.print(f"COMPATIBILITY_{category} {code} at {location}{suffix}")
