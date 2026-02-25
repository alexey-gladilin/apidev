from pathlib import Path

from apidev.application.dto.resolved_paths import resolve_paths
from apidev.application.dto.diagnostics import ValidationResult
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.rules.operation_id import ensure_unique_operation_ids


class ValidateService:
    def __init__(self, loader: ContractLoaderPort, config_loader: ConfigLoaderPort):
        self.loader = loader
        self.config_loader = config_loader

    def run(self, project_dir: Path) -> ValidationResult:
        result = ValidationResult()
        config = self.config_loader.load(project_dir)
        paths = resolve_paths(project_dir, config)
        operations = self.loader.load(paths.contracts_dir)
        result.operations = operations
        result.errors.extend(ensure_unique_operation_ids(operations))
        return result
