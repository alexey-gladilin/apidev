from pathlib import Path

from apidev.core.models.contract_document import ContractDocument
from apidev.core.rules.contract_schema import validate_contract_schema
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader


def _document(payload: dict[str, object]) -> ContractDocument:
    return ContractDocument(
        source_path=Path(".apidev/contracts/users/search.yaml"),
        contract_relpath=Path("users/search.yaml"),
        data=payload,
    )


def _valid_contract_payload() -> dict[str, object]:
    return {
        "method": "POST",
        "path": "/v1/users/search",
        "auth": "bearer",
        "summary": "Search users",
        "description": "Search users by filters.",
        "response": {"status": 200, "body": {"type": "object"}},
        "errors": [],
    }


def test_contract_schema_accepts_and_preserves_operation_metadata_fields() -> None:
    payload = _valid_contract_payload()
    payload["intent"] = "read"
    payload["access_pattern"] = "imperative"

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert diagnostics == []
    assert contract is not None
    assert contract.intent == "read"
    assert contract.access_pattern == "imperative"


def test_yaml_loader_does_not_apply_implicit_defaults_for_operation_metadata(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / ".apidev" / "contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)
    contract_path = contracts_root / "users" / "search.yaml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        """
method: POST
path: /v1/users/search
auth: bearer
description: Search users by filters.
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    operations = YamlContractLoader().load(contracts_root)

    assert len(operations) == 1
    assert operations[0].contract.intent is None
    assert operations[0].contract.access_pattern is None


def test_yaml_loader_preserves_explicit_operation_metadata_fields(tmp_path: Path) -> None:
    contracts_root = tmp_path / ".apidev" / "contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)
    contract_path = contracts_root / "users" / "search.yaml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        """
method: POST
path: /v1/users/search
auth: bearer
description: Search users by filters.
intent: read
access_pattern: imperative
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    operations = YamlContractLoader().load(contracts_root)

    assert len(operations) == 1
    assert operations[0].contract.intent == "read"
    assert operations[0].contract.access_pattern == "imperative"
