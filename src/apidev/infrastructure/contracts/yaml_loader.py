from pathlib import Path

import yaml

from apidev.core.models.contract import EndpointContract
from apidev.core.models.contract_document import ContractDocument
from apidev.core.models.operation import Operation
from apidev.core.ports.contract_document_loader import ContractDocumentLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.rules.operation_id import build_operation_id


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

            description = str(data.get("description", "")).strip()
            request = data.get("request", {}) if isinstance(data.get("request"), dict) else {}
            response = data.get("response", {}) if isinstance(data.get("response"), dict) else {}

            contract = EndpointContract(
                source_path=path,
                method=str(data.get("method", "GET")).upper(),
                path=str(data.get("path", "/")),
                auth=str(data.get("auth", "public")),
                description=description,
                response_status=int(response.get("status", 200)),
                response_body=response.get("body", {}),
                errors=data.get("errors", []),
                request_path=(
                    request.get("path", {}) if isinstance(request.get("path"), dict) else {}
                ),
                request_query=(
                    request.get("query", {}) if isinstance(request.get("query"), dict) else {}
                ),
                request_body=(
                    request.get("body", {}) if isinstance(request.get("body"), dict) else {}
                ),
            )
            operations.append(
                Operation(operation_id=operation_id, contract=contract, contract_relpath=rel)
            )

        return operations
