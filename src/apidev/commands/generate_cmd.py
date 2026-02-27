from pathlib import Path

from rich.console import Console

from apidev.application.services.generate_service import GenerateService
from apidev.application.services.validate_service import ValidateService
from apidev.commands.runtime import load_runtime
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.output.writer import SafeWriter
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer

console = Console()


def generate_command(project_dir: Path = Path("."), check: bool = False) -> None:
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

    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=contract_loader,
        renderer=JinjaTemplateRenderer(custom_templates_dir=paths.templates_dir),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )
    result = service.run(root, check=check)

    if result.drift_status == "drift":
        console.print("Drift detected (drift-status: drift)")
        raise SystemExit(1)

    if check:
        console.print("No drift (drift-status: no-drift)")
        return

    console.print(f"Applied changes: {result.applied_changes} (drift-status: no-drift)")
