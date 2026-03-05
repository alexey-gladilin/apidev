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
        "method": "GET",
        "path": "/v1/invoices/{invoice_id}",
        "auth": "bearer",
        "summary": "Get invoice",
        "description": "Get invoice",
        "response": {"status": 200, "body": {"type": "object"}},
        "errors": [],
    }


def test_contract_schema_rejects_path_placeholders_without_request_path() -> None:
    payload = _valid_contract_payload()

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [item.code for item in diagnostics] == ["validation.missing-request-path"]
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.path"


def test_contract_schema_rejects_when_request_path_is_missing_route_param() -> None:
    payload = _valid_contract_payload()
    payload["path"] = "/v1/invoices/{invoice_id}/{line_id}"
    payload["request"] = {
        "path": {
            "type": "object",
            "properties": {"invoice_id": {"type": "string", "required": True}},
        }
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [item.code for item in diagnostics] == ["validation.request-path-mismatch"]
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.path"


def test_contract_schema_rejects_when_request_path_has_extra_param() -> None:
    payload = _valid_contract_payload()
    payload["request"] = {
        "path": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "required": True},
                "line_id": {"type": "string", "required": True},
            },
        }
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [item.code for item in diagnostics] == ["validation.request-path-mismatch"]
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.path"


def test_contract_schema_matches_path_params_case_sensitively() -> None:
    payload = _valid_contract_payload()
    payload["path"] = "/v1/invoices/{InvoiceID}"
    payload["request"] = {
        "path": {
            "type": "object",
            "properties": {"invoiceid": {"type": "string", "required": True}},
        }
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [item.code for item in diagnostics] == ["validation.request-path-mismatch"]
    assert diagnostics[0].location == "billing/get_invoice.yaml:request.path"


def test_contract_schema_request_path_mismatch_duplicate_case_route_placeholders() -> None:
    payload = _valid_contract_payload()
    payload["path"] = "/v1/invoices/{invoice_id}/{invoice_id}"
    payload["request"] = {
        "path": {
            "type": "object",
            "properties": {"invoice_id": {"type": "string", "required": True}},
        }
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert [item.code for item in diagnostics] == ["validation.duplicate-path-placeholder"]
    assert diagnostics[0].location == "billing/get_invoice.yaml:path"


def test_contract_schema_accepts_legacy_contract_without_request_when_path_has_no_placeholders() -> (
    None
):
    payload = _valid_contract_payload()
    payload["path"] = "/v1/invoices/status"

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert diagnostics == []
    assert contract is not None
