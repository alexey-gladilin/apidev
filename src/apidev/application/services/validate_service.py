from pathlib import Path

from apidev.application.dto.diagnostics import ValidationResult
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.rules.operation_id import ensure_unique_operation_ids


class ValidateService:
    def __init__(self, loader: ContractLoaderPort):
        self.loader = loader

    def run(self, project_dir: Path) -> ValidationResult:
        result = ValidationResult()
        operations = self.loader.load(project_dir)
        result.operations = operations
        result.errors.extend(ensure_unique_operation_ids(operations))
        return result
