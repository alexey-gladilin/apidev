from pathlib import Path

import yaml

from apidev.core.models.contract import (
    EndpointContract,
)
from apidev.core.models.contract_document import ContractDocument
from apidev.core.models.operation import Operation
from apidev.core.ports.contract_document_loader import ContractDocumentLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.rules.operation_id import build_operation_id
from apidev.core.rules.contract_schema import validate_contract_schema


class YamlContractLoader(ContractLoaderPort, ContractDocumentLoaderPort):
    def load_documents(self, contracts_root: Path) -> list[ContractDocument]:
        if not contracts_root.exists():
            return []

        documents: list[ContractDocument] = []
        for path in sorted(contracts_root.rglob("*.yaml")):
            rel = path.relative_to(contracts_root)
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                documents.append(
                    ContractDocument(
                        source_path=path,
                        contract_relpath=rel,
                        data=None,
                        parse_error=str(exc),
                    )
                )
                continue

            documents.append(
                ContractDocument(
                    source_path=path,
                    contract_relpath=rel,
                    data={} if data is None else data,
                )
            )

        return documents

    def load(self, contracts_root: Path) -> list[Operation]:
        operations: list[Operation] = []
        for document in self.load_documents(contracts_root):
            if document.parse_error:
                raise ValueError(
                    f"Invalid YAML at {document.contract_relpath}: {document.parse_error}"
                )

            path = document.source_path
            rel = document.contract_relpath
            operation_id = build_operation_id(str(rel))
            data = document.data if isinstance(document.data, dict) else {}
            contract_type = str(data.get("contract_type", "operation")).strip().lower()
            if contract_type == "shared_model":
                continue
            if contract_type != "operation":
                raise ValueError(
                    f"Invalid contract_type '{contract_type}' at {rel}. "
                    "Expected 'operation' or 'shared_model'."
                )

            contract, diagnostics = validate_contract_schema(document)
            if contract is None:
                detail = "; ".join(
                    f"{diagnostic.location}: {diagnostic.message}" for diagnostic in diagnostics
                )
                raise ValueError(f"Invalid contract at {rel}: {detail}")
            operations.append(
                Operation(operation_id=operation_id, contract=contract, contract_relpath=rel)
            )

        return operations
