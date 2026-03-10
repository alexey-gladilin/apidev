from pathlib import Path

from apidev.core.models.contract_document import ContractDocument
from apidev.core.rules.contract_schema import validate_contract_schema


def _document(payload: dict[str, object]) -> ContractDocument:
    return ContractDocument(
        source_path=Path(".apidev/contracts/billing/get_invoice.yaml"),
        contract_relpath=Path("billing/get_invoice.yaml"),
        data=payload,
    )


def _valid_contract_payload() -> dict[str, object]:
    return {
        "method": "POST",
        "path": "/v1/invoices/{invoice_id}",
        "auth": "bearer",
        "summary": "Create invoice",
        "description": "Create invoice",
        "intent": "write",
        "access_pattern": "imperative",
        "response": {"status": 201, "body": {"type": "object"}},
        "errors": [],
    }


def test_contract_schema_request_null_is_treated_as_absent_request_block() -> None:
    payload = _valid_contract_payload()
    payload["request"] = None

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [item.code for item in diagnostics] == ["validation.missing-request-path"]
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.path"


def test_contract_schema_empty_request_mapping_is_accepted() -> None:
    payload = _valid_contract_payload()
    payload["request"] = {}

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [item.code for item in diagnostics] == ["validation.missing-request-path"]
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.path"
