from pathlib import Path
from typing import Any, cast

from apidev.application.services.diff_service import DiffService


def _create_service() -> DiffService:
    return DiffService(
        config_loader=cast(Any, None),
        loader=cast(Any, None),
        renderer=cast(Any, None),
        fs=cast(Any, None),
        postprocessor=cast(Any, None),
    )


def test_endpoint_contract_request_model_maps_normalized_request_fragments() -> None:
    service = _create_service()
    source_data = {
        "method": "post",
        "path": "/v1/invoices/{invoice_id}",
        "auth": "bearer",
        "summary": "Get invoice",
        "description": "Get invoice details",
        "request": {
            "path": {"type": "object", "properties": {"invoice_id": {"type": "string"}}},
            "query": {"type": "object", "properties": {"expand": {"type": "boolean"}}},
            "body": {
                "type": "object",
                "properties": {"comment": {"type": "string"}},
            },
        },
        "response": {
            "status": 200,
            "body": {"type": "object"},
        },
        "errors": [],
    }

    operation = service._build_operation_from_contract_data(
        contract_relpath=Path("billing/get_invoice.yaml"),
        data=source_data,
    )

    assert operation.contract.request_path == source_data["request"]["path"]
    assert operation.contract.request_query == source_data["request"]["query"]
    assert operation.contract.request_body == source_data["request"]["body"]


def test_endpoint_contract_request_model_defaults_to_empty_fragments_for_legacy_contract() -> None:
    service = _create_service()

    operation = service._build_operation_from_contract_data(
        contract_relpath=Path("billing/get_invoice.yaml"),
        data={
            "method": "GET",
            "path": "/v1/invoices/{invoice_id}",
            "auth": "bearer",
            "summary": "Get invoice",
            "description": "Get invoice details",
            "response": {"status": 200, "body": {"type": "object"}},
            "errors": [],
        },
    )

    assert operation.contract.request_path == {}
    assert operation.contract.request_query == {}
    assert operation.contract.request_body == {}


def test_endpoint_contract_request_model_ignores_invalid_request_fragment_shapes() -> None:
    service = _create_service()

    operation = service._build_operation_from_contract_data(
        contract_relpath=Path("billing/get_invoice.yaml"),
        data={
            "method": "GET",
            "path": "/v1/invoices/{invoice_id}",
            "auth": "bearer",
            "summary": "Get invoice",
            "description": "Get invoice details",
            "request": {
                "path": "invalid",
                "query": ["invalid"],
                "body": None,
            },
            "response": {"status": 200, "body": {"type": "object"}},
            "errors": [],
        },
    )

    assert operation.contract.request_path == {}
    assert operation.contract.request_query == {}
    assert operation.contract.request_body == {}


def test_endpoint_contract_request_model_canonicalizes_auth_mode() -> None:
    service = _create_service()

    operation = service._build_operation_from_contract_data(
        contract_relpath=Path("billing/get_invoice.yaml"),
        data={
            "method": "GET",
            "path": "/v1/invoices/{invoice_id}",
            "auth": "  BeAreR ",
            "summary": "Get invoice",
            "description": "Get invoice details",
            "response": {"status": 200, "body": {"type": "object"}},
            "errors": [],
        },
    )

    assert operation.contract.auth == "bearer"
