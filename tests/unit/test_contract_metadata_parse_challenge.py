from pathlib import Path

import pytest

from apidev.core.models.contract_document import ContractDocument
from apidev.core.rules.contract_schema import (
    SCHEMA_MISSING_FIELD,
    SCHEMA_INVALID_TYPE,
    SCHEMA_INVALID_VALUE,
    validate_contract_schema,
)
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


def test_yaml_loader_rejects_null_metadata_without_defaults(tmp_path: Path) -> None:
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
intent: null
access_pattern: null
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
        raise AssertionError("Expected YamlContractLoader to reject null metadata.")


def test_parse_stage_rejects_missing_metadata_fields() -> None:
    payload = _valid_contract_payload()
    payload.pop("intent")
    payload.pop("access_pattern")

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [diagnostic.code for diagnostic in diagnostics] == [
        SCHEMA_MISSING_FIELD,
        SCHEMA_MISSING_FIELD,
    ]
    assert [diagnostic.location for diagnostic in diagnostics] == [
        "users/search.yaml:intent",
        "users/search.yaml:access_pattern",
    ]


def test_parse_stage_rejects_null_metadata_fields() -> None:
    payload = _valid_contract_payload()
    payload["intent"] = None
    payload["access_pattern"] = None

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [diagnostic.code for diagnostic in diagnostics] == [
        SCHEMA_MISSING_FIELD,
        SCHEMA_MISSING_FIELD,
    ]
    assert [diagnostic.location for diagnostic in diagnostics] == [
        "users/search.yaml:intent",
        "users/search.yaml:access_pattern",
    ]


def test_parse_stage_rejects_empty_metadata_strings() -> None:
    payload = _valid_contract_payload()
    payload["intent"] = ""
    payload["access_pattern"] = "   "

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [diagnostic.code for diagnostic in diagnostics] == [
        SCHEMA_INVALID_VALUE,
        SCHEMA_INVALID_VALUE,
    ]
    assert [diagnostic.location for diagnostic in diagnostics] == [
        "users/search.yaml:intent",
        "users/search.yaml:access_pattern",
    ]


def test_parse_stage_preserves_metadata_values_outside_allowlist_for_semantic_validation() -> None:
    payload = _valid_contract_payload()
    payload["intent"] = "mutate"
    payload["access_pattern"] = "streaming"

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert diagnostics == []
    assert contract is not None
    assert contract.intent == "mutate"
    assert contract.access_pattern == "streaming"


@pytest.mark.parametrize("access_pattern", ["cached", "both"])
def test_parse_stage_preserves_write_with_read_only_access_patterns_for_semantic_validation(
    access_pattern: str,
) -> None:
    payload = _valid_contract_payload()
    payload["intent"] = "write"
    payload["access_pattern"] = access_pattern

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert diagnostics == []
    assert contract is not None
    assert contract.intent == "write"
    assert contract.access_pattern == access_pattern


def test_yaml_loader_rejects_metadata_values_outside_allowlist(tmp_path: Path) -> None:
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
intent: mutate
access_pattern: streaming
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
            "Field 'access_pattern' must be one of: both, cached, imperative, none.; "
            "Field 'intent' must be one of: read, write."
        )
    else:
        raise AssertionError("Expected YamlContractLoader to reject invalid metadata values.")


def test_parse_stage_rejects_non_string_metadata_types() -> None:
    payload = _valid_contract_payload()
    payload["intent"] = 1
    payload["access_pattern"] = ["imperative"]

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [diagnostic.code for diagnostic in diagnostics] == [
        SCHEMA_INVALID_TYPE,
        SCHEMA_INVALID_TYPE,
    ]
    assert [diagnostic.location for diagnostic in diagnostics] == [
        "users/search.yaml:intent",
        "users/search.yaml:access_pattern",
    ]


def test_yaml_loader_rejects_invalid_operation_metadata_combination(tmp_path: Path) -> None:
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
intent: write
access_pattern: cached
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
            "Field 'access_pattern' is incompatible with intent 'write'. "
            "Allowed values: imperative, none."
        )
    else:
        raise AssertionError("Expected YamlContractLoader to reject invalid metadata combination.")
