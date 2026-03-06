from pathlib import Path

from apidev.core.models.contract import EndpointContract
from apidev.core.models.contract_document import ContractDocument
from apidev.core.models.operation import Operation
from apidev.core.rules.contract_semantic import (
    build_normalized_model_registry,
    resolve_model_reference,
)


def _operation_with_local_model() -> Operation:
    return Operation(
        operation_id="billing_list_items",
        contract_relpath=Path("billing/list_items.yaml"),
        contract=EndpointContract(
            source_path=Path("billing/list_items.yaml"),
            method="GET",
            path="/v1/items",
            auth="public",
            description="list",
            response_status=200,
            response_body={"type": "object"},
            errors=[],
            local_models={
                "PageInfo": {"type": "object", "properties": {"total": {"type": "integer"}}}
            },
        ),
    )


def _shared_documents() -> list[ContractDocument]:
    return [
        ContractDocument(
            source_path=Path(".apidev/models/billing/page_info.yaml"),
            contract_relpath=Path("billing/page_info.yaml"),
            data={
                "contract_type": "shared_model",
                "name": "PageInfo",
                "description": "billing page info",
                "model": {"type": "object", "properties": {"page": {"type": "integer"}}},
            },
        )
    ]


def test_build_normalized_registry_collects_shared_and_local_models() -> None:
    diagnostics = []
    registry = build_normalized_model_registry(
        operations=[_operation_with_local_model()],
        shared_model_documents=_shared_documents(),
        diagnostics=diagnostics,
    )

    assert diagnostics == []
    assert "billing.PageInfo" in registry.shared_models
    assert "local_model:billing_list_items.PageInfo" in registry.local_models
    assert registry.shared_by_short["PageInfo"] == ["billing.PageInfo"]


def test_resolver_is_deterministic_without_common_namespace_special_case() -> None:
    diagnostics = []
    registry = build_normalized_model_registry(
        operations=[_operation_with_local_model()],
        shared_model_documents=_shared_documents(),
        diagnostics=diagnostics,
    )

    # Short reference must resolve to local model for owner operation.
    kind, target = resolve_model_reference(
        ref_raw="PageInfo",
        context_kind="operation",
        owner_operation_id="billing_list_items",
        owner_local_models={"PageInfo"},
        registry=registry,
    )
    assert (kind, target) == ("resolved", "local_model:billing_list_items.PageInfo")

    # Fully-qualified reference must resolve to shared model directly.
    fq_kind, fq_target = resolve_model_reference(
        ref_raw="billing.PageInfo",
        context_kind="operation",
        owner_operation_id="billing_list_items",
        owner_local_models={"PageInfo"},
        registry=registry,
    )
    assert (fq_kind, fq_target) == ("resolved", "shared_model:billing.PageInfo")
