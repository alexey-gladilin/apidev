from pathlib import Path

from rich.console import Console

from apidev.application.services.diff_service import DiffService
from apidev.application.services.validate_service import ValidateService
from apidev.commands.runtime import load_runtime
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

console = Console()


def diff_command(project_dir: Path = Path(".")) -> None:
    root = project_dir.resolve()
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
    plan = service.run(root)

    if not plan.changes:
        console.print("No changes")
        return

    for change in plan.changes:
        console.print(f"{change.change_type:>7} {change.path}")
