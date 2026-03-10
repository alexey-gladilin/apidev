from pathlib import Path

from apidev.core.models.contract_document import ContractDocument
from apidev.core.rules.contract_schema import validate_contract_schema


def _document(payload: object, relpath: str = "models/common/pagination.yaml") -> ContractDocument:
    return ContractDocument(
        source_path=Path("/tmp") / relpath,
        contract_relpath=Path(relpath),
        data=payload,
    )


def test_validate_accepts_shared_model_contract_file() -> None:
    payload = {
        "contract_type": "shared_model",
        "name": "PaginationRequest",
        "description": "Pagination payload.",
        "model": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "required": True},
                "size": {"type": "integer", "required": True},
            },
        },
    }

    contract, diagnostics = validate_contract_schema(_document(payload))

    assert contract is None
    assert diagnostics == []


def test_validate_accepts_ref_nodes_and_items_ref_shorthand() -> None:
    payload = {
        "method": "POST",
        "path": "/v1/users/search",
        "auth": "bearer",
        "intent": "read",
        "access_pattern": "imperative",
        "description": "Search users.",
        "request": {
            "body": {
                "type": "object",
                "properties": {
                    "pagination": {"$ref": "common.PaginationRequest", "required": False},
                    "items": {
                        "type": "array",
                        "items": "$users.UserSummary",
                    },
                },
            }
        },
        "response": {
            "status": 200,
            "body": {"$ref": "users.SearchResult"},
        },
        "errors": [],
    }

    contract, diagnostics = validate_contract_schema(
        _document(payload, "contracts/users/search.yaml")
    )

    assert contract is not None
    assert diagnostics == []


def test_validate_rejects_ref_node_with_inline_shape_fields() -> None:
    payload = {
        "method": "GET",
        "path": "/v1/users",
        "auth": "bearer",
        "intent": "read",
        "access_pattern": "cached",
        "description": "List users.",
        "response": {
            "status": 200,
            "body": {
                "$ref": "users.User",
                "type": "object",
            },
        },
        "errors": [],
    }

    contract, diagnostics = validate_contract_schema(
        _document(payload, "contracts/users/list.yaml")
    )

    assert contract is None
    assert any(d.code == "SCHEMA_INVALID_VALUE" for d in diagnostics)
    assert any(d.location.endswith("response.body.type") for d in diagnostics)


def test_validate_rejects_ref_node_with_null_ref_value() -> None:
    payload = {
        "method": "GET",
        "path": "/v1/users",
        "auth": "bearer",
        "intent": "read",
        "access_pattern": "cached",
        "description": "List users.",
        "response": {
            "status": 200,
            "body": {
                "$ref": None,
            },
        },
        "errors": [],
    }

    contract, diagnostics = validate_contract_schema(
        _document(payload, "contracts/users/list_null_ref.yaml")
    )

    assert contract is None
    assert any(d.location.endswith("response.body.$ref") for d in diagnostics)
