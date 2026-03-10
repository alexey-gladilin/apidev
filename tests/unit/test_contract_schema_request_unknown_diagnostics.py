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


def test_contract_schema_request_supports_path_query_and_body_fragments() -> None:
    payload = _valid_contract_payload()
    payload["request"] = {
        "path": {
            "type": "object",
            "properties": {"invoice_id": {"type": "string", "required": True}},
        },
        "query": {
            "type": "object",
            "properties": {"expand": {"type": "boolean"}},
        },
        "body": {
            "type": "object",
            "properties": {"currency": {"type": "string", "required": True}},
        },
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert diagnostics == []
    assert contract is not None


def test_contract_schema_request_unknown_field_uses_validation_diagnostics_code() -> None:
    payload = _valid_contract_payload()
    payload["request"] = {
        "path": {
            "type": "object",
            "properties": {"invoice_id": {"type": "string", "required": True}},
            "unknown_schema_key": True,
        }
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert diagnostics
    assert diagnostics[0].code == "validation.request-unknown-field"
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.path.unknown_schema_key"


def test_contract_schema_request_unknown_root_field_has_precise_path_and_stable_diagnostics() -> (
    None
):
    payload = _valid_contract_payload()
    payload["request"] = {
        "path": {"type": "object", "properties": {}},
        "headers": {"type": "object", "properties": {}},
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert diagnostics
    assert diagnostics[0].code == "validation.request-unknown-field"
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.headers"


def test_contract_schema_request_unknown_root_field_fail_fast_skips_other_request_diagnostics() -> (
    None
):
    payload = _valid_contract_payload()
    payload["request"] = {
        "headers": {"type": "object", "properties": {}},
        "query": "invalid",
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert diagnostics
    assert {diagnostic.code for diagnostic in diagnostics} == {"validation.request-unknown-field"}
    assert [diagnostic.location for diagnostic in diagnostics] == [
        "billing/get_invoice.yaml:request.headers"
    ]
