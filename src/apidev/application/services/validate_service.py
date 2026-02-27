from pathlib import Path

from apidev.application.dto.resolved_paths import resolve_paths
from apidev.application.dto.diagnostics import ValidationResult
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_document_loader import ContractDocumentLoaderPort
from apidev.core.rules.contract_schema import validate_contract_schema
from apidev.core.rules.contract_semantic import validate_semantic_rules
from apidev.core.rules.operation_id import build_operation_id
from apidev.core.models.operation import Operation


class ValidateService:
    def __init__(self, loader: ContractDocumentLoaderPort, config_loader: ConfigLoaderPort):
        self.loader = loader
        self.config_loader = config_loader

    def run(self, project_dir: Path) -> ValidationResult:
        result = ValidationResult()
        config = self.config_loader.load(project_dir)
        paths = resolve_paths(project_dir, config)

        operations: list[Operation] = []
        for document in self.loader.load_documents(paths.contracts_dir):
            contract, schema_diagnostics = validate_contract_schema(document)
            result.diagnostics.extend(schema_diagnostics)
            if contract is None:
                continue

            operations.append(
                Operation(
                    operation_id=build_operation_id(document.contract_relpath.as_posix()),
                    contract=contract,
                    contract_relpath=document.contract_relpath,
                )
            )

        result.operations = operations
        result.diagnostics.extend(validate_semantic_rules(operations))
        result.diagnostics.sort(key=lambda diagnostic: (diagnostic.location, diagnostic.code))
        return result
