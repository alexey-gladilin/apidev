from pathlib import Path
from typing import NoReturn

import yaml

from apidev.core.models.contract_document import ContractDocument
from apidev.core.models.operation import Operation
from apidev.core.ports.contract_document_loader import ContractDocumentLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.rules.contract_schema import validate_contract_schema
from apidev.core.rules.contract_semantic import validate_operation_metadata_semantics
from apidev.core.rules.operation_id import build_operation_id


class YamlContractLoader(ContractLoaderPort, ContractDocumentLoaderPort):
    @staticmethod
    def _raise_invalid_contract(relpath: Path, detail: str) -> NoReturn:
        raise ValueError(f"Invalid contract at {relpath}: {detail}")

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
            rel = document.contract_relpath
            operation_id = build_operation_id(str(rel))
            data = document.data if isinstance(document.data, dict) else {}
            contract_type = str(data.get("contract_type", "operation")).strip().lower()
            if contract_type == "shared_model":
                continue
            contract, diagnostics = validate_contract_schema(document)
            if diagnostics:
                detail = "; ".join(diagnostic.message for diagnostic in diagnostics)
                self._raise_invalid_contract(rel, detail)
            if contract is None:
                self._raise_invalid_contract(rel, "contract validation returned no data.")

            operation = Operation(
                operation_id=operation_id,
                contract=contract,
                contract_relpath=rel,
            )
            semantic_diagnostics = validate_operation_metadata_semantics(operation)
            if semantic_diagnostics:
                semantic_diagnostics.sort(
                    key=lambda diagnostic: (diagnostic.location, diagnostic.normalized_code())
                )
                detail = "; ".join(diagnostic.message for diagnostic in semantic_diagnostics)
                self._raise_invalid_contract(rel, detail)

            operations.append(operation)

        return operations
