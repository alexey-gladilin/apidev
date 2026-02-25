from pathlib import Path

import yaml

from apidev.core.models.contract import EndpointContract
from apidev.core.models.operation import Operation
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.rules.operation_id import build_operation_id


class YamlContractLoader(ContractLoaderPort):
    def load(self, project_dir: Path) -> list[Operation]:
        contracts_root = project_dir / ".apidev" / "contracts"
        if not contracts_root.exists():
            return []

        operations: list[Operation] = []
        for path in sorted(contracts_root.rglob("*.yaml")):
            rel = path.relative_to(contracts_root)
            operation_id = build_operation_id(str(rel))
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

            contract = EndpointContract(
                source_path=path,
                method=str(data.get("method", "GET")).upper(),
                path=str(data.get("path", "/")),
                auth=str(data.get("auth", "public")),
                summary=str(data.get("summary", "")),
                description=str(data.get("description", "")),
                response_status=int(data.get("response", {}).get("status", 200)),
                response_body=data.get("response", {}).get("body", {}),
                errors=data.get("errors", []),
            )
            operations.append(
                Operation(operation_id=operation_id, contract=contract, contract_relpath=rel)
            )

        return operations
