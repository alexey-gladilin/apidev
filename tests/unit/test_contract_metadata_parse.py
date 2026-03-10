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
        "intent": "read",
        "access_pattern": "imperative",
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


def test_yaml_loader_rejects_missing_operation_metadata_without_defaulting(
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

    try:
        YamlContractLoader().load(contracts_root)
    except ValueError as exc:
        assert str(exc) == (
            "Invalid contract at users/search.yaml: "
            "Missing required field 'intent'.; "
            "Missing required field 'access_pattern'."
        )
    else:
        raise AssertionError("Expected YamlContractLoader to reject missing metadata.")


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


def test_yaml_loader_rejects_non_string_operation_metadata(tmp_path: Path) -> None:
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
intent: 1
access_pattern:
  - imperative
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    try:
        YamlContractLoader().load(contracts_root)
    except ValueError as exc:
        assert (
            str(exc) == "Invalid contract at users/search.yaml: "
            "Field 'intent' must be of type str, got int.; "
            "Field 'access_pattern' must be of type str, got list."
        )
    else:
        raise AssertionError("Expected YamlContractLoader to reject non-string metadata.")


def test_yaml_loader_rejects_schema_invalid_contract_without_defaulting(tmp_path: Path) -> None:
    contracts_root = tmp_path / ".apidev" / "contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)
    contract_path = contracts_root / "users" / "search.yaml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        """
description: Search users by filters.
intent: read
access_pattern: imperative
""".strip(),
        encoding="utf-8",
    )

    try:
        YamlContractLoader().load(contracts_root)
    except ValueError as exc:
        assert str(exc) == (
            "Invalid contract at users/search.yaml: Missing required field 'method'.; "
            "Missing required field 'path'.; Missing required field 'auth'.; "
            "Missing required field 'response'.; Missing required field 'errors'."
        )
    else:
        raise AssertionError("Expected YamlContractLoader to reject schema-invalid contract.")
