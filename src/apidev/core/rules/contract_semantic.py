from collections import defaultdict
import re
from dataclasses import dataclass
from typing import Any

from apidev.core.models.contract_document import ContractDocument
from apidev.core.models.diagnostic import ValidationDiagnostic
from apidev.core.models.operation import Operation

SEMANTIC_DUPLICATE_OPERATION_ID = "SEMANTIC_DUPLICATE_OPERATION_ID"
SEMANTIC_INVALID_OPERATION_ID = "SEMANTIC_INVALID_OPERATION_ID"
SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE = "SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE"
SEMANTIC_CONTRACT_TYPE_LOCATION_MISMATCH = "SEMANTIC_CONTRACT_TYPE_LOCATION_MISMATCH"
SEMANTIC_MISSING_MODEL_REFERENCE = "SEMANTIC_MISSING_MODEL_REFERENCE"
SEMANTIC_AMBIGUOUS_MODEL_REFERENCE = "SEMANTIC_AMBIGUOUS_MODEL_REFERENCE"
SEMANTIC_SCOPE_LEAK = "SEMANTIC_SCOPE_LEAK"
SEMANTIC_DUPLICATE_SHARED_MODEL_NAME = "SEMANTIC_DUPLICATE_SHARED_MODEL_NAME"
SEMANTIC_CONTRACT_REFERENCE_CYCLE = "validation.CONTRACT_REFERENCE_CYCLE"
RULE_OPERATION_ID_UNIQUE = "semantic.operation_id.unique"
RULE_OPERATION_ID_FORMAT = "semantic.operation_id.format"
RULE_ENDPOINT_SIGNATURE_UNIQUE = "semantic.endpoint_signature.unique"
RULE_CONTRACT_TYPE_LOCATION = "semantic.contract_type.location"
RULE_MODEL_REF_RESOLUTION = "semantic.model_ref.resolution"
RULE_SCOPE_BOUNDARY = "semantic.model_ref.scope"
RULE_SHARED_MODEL_UNIQUE = "semantic.shared_model.unique"
RULE_MODEL_GRAPH_ACYCLIC = "semantic.model_graph.acyclic"
OPERATION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(slots=True)
class _SharedModelDef:
    key: str
    short_name: str
    location: str
    schema: dict[str, Any]


@dataclass(slots=True)
class _RefEdge:
    source_node: str
    source_location: str
    ref_raw: str
    ref_location: str
    context_kind: str
    owner_operation_id: str | None = None
    owner_local_models: set[str] | None = None


@dataclass(slots=True)
class _NormalizedModelRegistry:
    shared_models: dict[str, _SharedModelDef]
    shared_by_short: dict[str, list[str]]
    local_models: dict[str, tuple[str, str, dict[str, Any]]]
    local_name_owners: dict[str, set[str]]
    node_locations: dict[str, str]


def build_normalized_model_registry(
    *,
    operations: list[Operation],
    shared_model_documents: list[ContractDocument],
    diagnostics: list[ValidationDiagnostic],
) -> _NormalizedModelRegistry:
    shared_models = _collect_shared_models(shared_model_documents, diagnostics)
    shared_by_short: dict[str, list[str]] = defaultdict(list)
    for model in shared_models.values():
        shared_by_short[model.short_name].append(model.key)
    for keys in shared_by_short.values():
        keys.sort()

    local_models: dict[str, tuple[str, str, dict[str, Any]]] = {}
    local_name_owners: dict[str, set[str]] = defaultdict(set)
    for operation in operations:
        for name, schema in sorted(operation.contract.local_models.items()):
            node_id = _local_node_id(operation.operation_id, name)
            location = operation.contract_relpath.as_posix()
            local_models[node_id] = (operation.operation_id, location, schema)
            local_name_owners[name].add(operation.operation_id)

    node_locations: dict[str, str] = {}
    for model in shared_models.values():
        node_locations[f"shared_model:{model.key}"] = f"{model.location}:model"
    for node_id, (_, location, _) in local_models.items():
        node_locations[node_id] = location

    return _NormalizedModelRegistry(
        shared_models=shared_models,
        shared_by_short=dict(shared_by_short),
        local_models=local_models,
        local_name_owners=dict(local_name_owners),
        node_locations=node_locations,
    )


def resolve_model_reference(
    *,
    ref_raw: str,
    context_kind: str,
    owner_operation_id: str | None,
    owner_local_models: set[str] | None,
    registry: _NormalizedModelRegistry,
) -> tuple[str, str]:
    edge = _RefEdge(
        source_node="manual:resolver",
        source_location="manual:resolver",
        ref_raw=ref_raw,
        ref_location="manual:resolver",
        context_kind=context_kind,
        owner_operation_id=owner_operation_id,
        owner_local_models=owner_local_models,
    )
    resolution = _resolve_ref(edge=edge, registry=registry)
    if resolution is None:
        return ("missing", "")
    return resolution


def build_dependency_graph(
    *,
    operations: list[Operation],
    operation_documents: list[ContractDocument],
    shared_model_documents: list[ContractDocument],
) -> dict[str, list[dict[str, str]]]:
    diagnostics: list[ValidationDiagnostic] = []
    registry = build_normalized_model_registry(
        operations=operations,
        shared_model_documents=shared_model_documents,
        diagnostics=diagnostics,
    )

    nodes: dict[str, dict[str, str]] = {}
    for operation in operations:
        node_id = f"operation:{operation.operation_id}"
        nodes[node_id] = {
            "id": node_id,
            "kind": "operation",
            "location": operation.contract_relpath.as_posix(),
        }
    for shared_key, shared_model in sorted(registry.shared_models.items()):
        node_id = f"shared_model:{shared_key}"
        nodes[node_id] = {
            "id": node_id,
            "kind": "shared_model",
            "location": shared_model.location,
        }
    for local_node, (owner_operation_id, location, _) in sorted(registry.local_models.items()):
        nodes[local_node] = {
            "id": local_node,
            "kind": "local_model",
            "location": location,
            "owner_operation_id": owner_operation_id,
        }

    edges: list[_RefEdge] = []
    for operation in operations:
        source_node = f"operation:{operation.operation_id}"
        local_names = set(operation.contract.local_models)
        base_location = operation.contract_relpath.as_posix()
        _collect_refs_from_schema(
            operation.contract.request_path,
            f"{base_location}:request.path",
            source_node,
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )
        _collect_refs_from_schema(
            operation.contract.request_query,
            f"{base_location}:request.query",
            source_node,
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )
        _collect_refs_from_schema(
            operation.contract.request_body,
            f"{base_location}:request.body",
            source_node,
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )
        _collect_refs_from_schema(
            operation.contract.response_body,
            f"{base_location}:response.body",
            source_node,
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )

        for index, error_item in enumerate(operation.contract.errors):
            body_schema = error_item.get("body")
            if isinstance(body_schema, dict):
                _collect_refs_from_schema(
                    body_schema,
                    f"{base_location}:errors[{index}].body",
                    source_node,
                    edges,
                    context_kind="operation",
                    owner_operation_id=operation.operation_id,
                    owner_local_models=local_names,
                )

        for local_name, local_schema in sorted(operation.contract.local_models.items()):
            _collect_refs_from_schema(
                local_schema,
                f"{base_location}:local_models.{local_name}",
                _local_node_id(operation.operation_id, local_name),
                edges,
                context_kind="local_model",
                owner_operation_id=operation.operation_id,
                owner_local_models=local_names,
            )

    for shared_key, shared_model in sorted(registry.shared_models.items()):
        _collect_refs_from_schema(
            shared_model.schema,
            f"{shared_model.location}:model",
            f"shared_model:{shared_key}",
            edges,
            context_kind="shared_model",
            owner_operation_id=None,
            owner_local_models=set(),
        )

    resolved_edges: list[dict[str, str]] = []
    unresolved_edges: list[dict[str, str]] = []
    for edge in edges:
        resolution = _resolve_ref(edge=edge, registry=registry)
        if resolution is None:
            continue
        kind, target = resolution
        if kind == "resolved":
            resolved_edges.append(
                {
                    "source": edge.source_node,
                    "target": target,
                    "ref": edge.ref_raw,
                    "location": edge.ref_location,
                }
            )
            continue
        unresolved_edges.append(
            {
                "source": edge.source_node,
                "ref": edge.ref_raw,
                "location": edge.ref_location,
                "reason": kind,
            }
        )

    _ = operation_documents
    return {
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(
            resolved_edges,
            key=lambda item: (item["source"], item["target"], item["location"], item["ref"]),
        ),
        "unresolved": sorted(
            unresolved_edges,
            key=lambda item: (item["source"], item["reason"], item["location"], item["ref"]),
        ),
    }


def validate_semantic_rules(
    operations: list[Operation],
    *,
    operation_documents: list[ContractDocument] | None = None,
    shared_model_documents: list[ContractDocument] | None = None,
) -> list[ValidationDiagnostic]:
    by_operation_id: dict[str, list[Operation]] = defaultdict(list)
    by_endpoint_signature: dict[tuple[str, str], list[Operation]] = defaultdict(list)
    for operation in operations:
        by_operation_id[operation.operation_id].append(operation)
        key = (operation.contract.method, operation.contract.path)
        by_endpoint_signature[key].append(operation)

    diagnostics: list[ValidationDiagnostic] = []
    for operation in operations:
        if OPERATION_ID_PATTERN.fullmatch(operation.operation_id):
            continue
        diagnostics.append(
            ValidationDiagnostic(
                code=SEMANTIC_INVALID_OPERATION_ID,
                severity="error",
                message=(
                    f"Invalid operation_id '{operation.operation_id}'. "
                    "Use lower_snake_case with leading letter."
                ),
                location=operation.contract_relpath.as_posix(),
                rule=RULE_OPERATION_ID_FORMAT,
            )
        )

    for operation_id in sorted(by_operation_id):
        bucket = by_operation_id[operation_id]
        if len(bucket) < 2:
            continue

        locations = sorted(operation.contract_relpath.as_posix() for operation in bucket)
        diagnostics.append(
            ValidationDiagnostic(
                code=SEMANTIC_DUPLICATE_OPERATION_ID,
                severity="error",
                message=f"Duplicate operation_id '{operation_id}'.",
                location=",".join(locations),
                rule=RULE_OPERATION_ID_UNIQUE,
            )
        )

    for method_path in sorted(by_endpoint_signature):
        bucket = by_endpoint_signature[method_path]
        if len(bucket) < 2:
            continue

        method, path = method_path
        locations = sorted(operation.contract_relpath.as_posix() for operation in bucket)
        diagnostics.append(
            ValidationDiagnostic(
                code=SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE,
                severity="error",
                message=f"Duplicate endpoint signature '{method} {path}'.",
                location=",".join(locations),
                rule=RULE_ENDPOINT_SIGNATURE_UNIQUE,
            )
        )

    if operation_documents is not None and shared_model_documents is not None:
        diagnostics.extend(
            _validate_shared_model_semantics(
                operations=operations,
                operation_documents=operation_documents,
                shared_model_documents=shared_model_documents,
            )
        )

    return diagnostics


def _validate_shared_model_semantics(
    *,
    operations: list[Operation],
    operation_documents: list[ContractDocument],
    shared_model_documents: list[ContractDocument],
) -> list[ValidationDiagnostic]:
    diagnostics: list[ValidationDiagnostic] = []
    diagnostics.extend(
        _validate_contract_type_locations(operation_documents, shared_model_documents)
    )

    registry = build_normalized_model_registry(
        operations=operations,
        shared_model_documents=shared_model_documents,
        diagnostics=diagnostics,
    )

    edges: list[_RefEdge] = []
    for operation in operations:
        local_names = set(operation.contract.local_models)
        base_location = operation.contract_relpath.as_posix()
        _collect_refs_from_schema(
            operation.contract.request_path,
            f"{base_location}:request.path",
            f"operation:{operation.operation_id}",
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )
        _collect_refs_from_schema(
            operation.contract.request_query,
            f"{base_location}:request.query",
            f"operation:{operation.operation_id}",
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )
        _collect_refs_from_schema(
            operation.contract.request_body,
            f"{base_location}:request.body",
            f"operation:{operation.operation_id}",
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )
        _collect_refs_from_schema(
            operation.contract.response_body,
            f"{base_location}:response.body",
            f"operation:{operation.operation_id}",
            edges,
            context_kind="operation",
            owner_operation_id=operation.operation_id,
            owner_local_models=local_names,
        )
        for index, error_item in enumerate(operation.contract.errors):
            body_schema = error_item.get("body")
            if isinstance(body_schema, dict):
                _collect_refs_from_schema(
                    body_schema,
                    f"{base_location}:errors[{index}].body",
                    f"operation:{operation.operation_id}",
                    edges,
                    context_kind="operation",
                    owner_operation_id=operation.operation_id,
                    owner_local_models=local_names,
                )
        for local_name, local_schema in sorted(operation.contract.local_models.items()):
            _collect_refs_from_schema(
                local_schema,
                f"{base_location}:local_models.{local_name}",
                _local_node_id(operation.operation_id, local_name),
                edges,
                context_kind="local_model",
                owner_operation_id=operation.operation_id,
                owner_local_models=local_names,
            )

    for model in registry.shared_models.values():
        _collect_refs_from_schema(
            model.schema,
            f"{model.location}:model",
            f"shared_model:{model.key}",
            edges,
            context_kind="shared_model",
            owner_operation_id=None,
            owner_local_models=set(),
        )

    model_graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        resolution = _resolve_ref(edge=edge, registry=registry)
        if resolution is None:
            continue
        kind, target = resolution
        if kind == "missing":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SEMANTIC_MISSING_MODEL_REFERENCE,
                    severity="error",
                    message=f"Reference '{edge.ref_raw}' cannot be resolved.",
                    location=edge.ref_location,
                    rule=RULE_MODEL_REF_RESOLUTION,
                )
            )
            continue
        if kind == "ambiguous":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SEMANTIC_AMBIGUOUS_MODEL_REFERENCE,
                    severity="error",
                    message=f"Reference '{edge.ref_raw}' is ambiguous across shared models.",
                    location=edge.ref_location,
                    rule=RULE_MODEL_REF_RESOLUTION,
                )
            )
            continue
        if kind == "scope_leak":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SEMANTIC_SCOPE_LEAK,
                    severity="error",
                    message=f"Reference '{edge.ref_raw}' violates shared/local scope boundaries.",
                    location=edge.ref_location,
                    rule=RULE_SCOPE_BOUNDARY,
                )
            )
            continue
        if edge.source_node.startswith(("shared_model:", "local_model:")):
            model_graph[edge.source_node].add(target)

    diagnostics.extend(_detect_reference_cycles(model_graph, registry.node_locations))
    return diagnostics


def _validate_contract_type_locations(
    operation_documents: list[ContractDocument], shared_model_documents: list[ContractDocument]
) -> list[ValidationDiagnostic]:
    diagnostics: list[ValidationDiagnostic] = []
    for document in operation_documents:
        if document.parse_error or not isinstance(document.data, dict):
            continue
        contract_type = str(document.data.get("contract_type", "operation")).strip().lower()
        if contract_type == "shared_model":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SEMANTIC_CONTRACT_TYPE_LOCATION_MISMATCH,
                    severity="error",
                    message=(
                        "Shared model contract is in operations directory; move it to "
                        "contracts.shared_models_dir."
                    ),
                    location=document.contract_relpath.as_posix(),
                    rule=RULE_CONTRACT_TYPE_LOCATION,
                )
            )

    for document in shared_model_documents:
        if document.parse_error or not isinstance(document.data, dict):
            continue
        contract_type = str(document.data.get("contract_type", "operation")).strip().lower()
        if contract_type != "shared_model":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SEMANTIC_CONTRACT_TYPE_LOCATION_MISMATCH,
                    severity="error",
                    message=(
                        "Operation contract is in shared models directory; move it to "
                        "contracts.dir."
                    ),
                    location=document.contract_relpath.as_posix(),
                    rule=RULE_CONTRACT_TYPE_LOCATION,
                )
            )

    return diagnostics


def _collect_shared_models(
    shared_model_documents: list[ContractDocument], diagnostics: list[ValidationDiagnostic]
) -> dict[str, _SharedModelDef]:
    models: dict[str, _SharedModelDef] = {}
    duplicates: dict[str, list[str]] = defaultdict(list)
    for document in shared_model_documents:
        if document.parse_error or not isinstance(document.data, dict):
            continue
        contract_type = str(document.data.get("contract_type", "operation")).strip().lower()
        if contract_type != "shared_model":
            continue
        raw_name = document.data.get("name")
        model_schema = document.data.get("model")
        if (
            not isinstance(raw_name, str)
            or not raw_name.strip()
            or not isinstance(model_schema, dict)
        ):
            continue
        namespace = document.contract_relpath.parent.as_posix().replace("/", ".").strip(".")
        key = f"{namespace}.{raw_name.strip()}" if namespace else raw_name.strip()
        location = document.contract_relpath.as_posix()
        duplicates[key].append(location)
        if key not in models:
            models[key] = _SharedModelDef(
                key=key,
                short_name=raw_name.strip(),
                location=location,
                schema=model_schema,
            )

    for key, locations in sorted(duplicates.items()):
        if len(locations) < 2:
            continue
        diagnostics.append(
            ValidationDiagnostic(
                code=SEMANTIC_DUPLICATE_SHARED_MODEL_NAME,
                severity="error",
                message=f"Duplicate shared model key '{key}'.",
                location=",".join(sorted(locations)),
                rule=RULE_SHARED_MODEL_UNIQUE,
            )
        )
    return models


def _collect_refs_from_schema(
    schema: Any,
    location_prefix: str,
    source_node: str,
    edges: list[_RefEdge],
    *,
    context_kind: str,
    owner_operation_id: str | None,
    owner_local_models: set[str] | None,
) -> None:
    if not isinstance(schema, dict):
        return

    ref_value = schema.get("$ref")
    if isinstance(ref_value, str):
        edges.append(
            _RefEdge(
                source_node=source_node,
                source_location=location_prefix,
                ref_raw=ref_value,
                ref_location=f"{location_prefix}.$ref",
                context_kind=context_kind,
                owner_operation_id=owner_operation_id,
                owner_local_models=owner_local_models,
            )
        )

    properties = schema.get("properties")
    if isinstance(properties, dict):
        for prop_name, prop_schema in sorted(properties.items()):
            prop_location = f"{location_prefix}.properties.{prop_name}"
            if isinstance(prop_schema, str) and prop_schema.startswith("$"):
                edges.append(
                    _RefEdge(
                        source_node=source_node,
                        source_location=location_prefix,
                        ref_raw=prop_schema[1:],
                        ref_location=prop_location,
                        context_kind=context_kind,
                        owner_operation_id=owner_operation_id,
                        owner_local_models=owner_local_models,
                    )
                )
            elif isinstance(prop_schema, dict):
                _collect_refs_from_schema(
                    prop_schema,
                    prop_location,
                    source_node,
                    edges,
                    context_kind=context_kind,
                    owner_operation_id=owner_operation_id,
                    owner_local_models=owner_local_models,
                )

    items = schema.get("items")
    if isinstance(items, str) and items.startswith("$"):
        edges.append(
            _RefEdge(
                source_node=source_node,
                source_location=location_prefix,
                ref_raw=items[1:],
                ref_location=f"{location_prefix}.items",
                context_kind=context_kind,
                owner_operation_id=owner_operation_id,
                owner_local_models=owner_local_models,
            )
        )
    elif isinstance(items, dict):
        _collect_refs_from_schema(
            items,
            f"{location_prefix}.items",
            source_node,
            edges,
            context_kind=context_kind,
            owner_operation_id=owner_operation_id,
            owner_local_models=owner_local_models,
        )


def _resolve_ref(
    *,
    edge: _RefEdge,
    registry: _NormalizedModelRegistry,
) -> tuple[str, str] | None:
    ref = edge.ref_raw.strip()
    if ref.startswith("$"):
        ref = ref[1:]
    if not ref:
        return ("missing", "")

    if "." in ref:
        if ref in registry.shared_models:
            return ("resolved", f"shared_model:{ref}")
        return ("missing", "")

    local_names = edge.owner_local_models or set()
    if edge.context_kind in {"operation", "local_model"} and ref in local_names:
        if edge.owner_operation_id is None:
            return ("missing", "")
        return ("resolved", _local_node_id(edge.owner_operation_id, ref))

    candidates = registry.shared_by_short.get(ref, [])
    if len(candidates) == 1:
        return ("resolved", f"shared_model:{candidates[0]}")
    if len(candidates) > 1:
        return ("ambiguous", "")

    if ref in registry.local_name_owners:
        return ("scope_leak", "")
    return ("missing", "")


def _detect_reference_cycles(
    model_graph: dict[str, set[str]], node_locations: dict[str, str]
) -> list[ValidationDiagnostic]:
    diagnostics: list[ValidationDiagnostic] = []
    visited: set[str] = set()
    stack: list[str] = []
    stack_set: set[str] = set()
    reported: set[tuple[str, ...]] = set()

    def dfs(node: str) -> None:
        visited.add(node)
        stack.append(node)
        stack_set.add(node)
        for neighbor in sorted(model_graph.get(node, set())):
            if neighbor not in visited:
                dfs(neighbor)
                continue
            if neighbor not in stack_set:
                continue
            start_idx = stack.index(neighbor)
            cycle_path = stack[start_idx:] + [neighbor]
            cycle_key = tuple(cycle_path)
            if cycle_key in reported:
                continue
            reported.add(cycle_key)
            diagnostics.append(
                ValidationDiagnostic(
                    code=SEMANTIC_CONTRACT_REFERENCE_CYCLE,
                    severity="error",
                    message=f"Reference cycle detected: {' -> '.join(cycle_path)}.",
                    location=node_locations.get(node, node),
                    rule=RULE_MODEL_GRAPH_ACYCLIC,
                    context={
                        "cycle_path": cycle_path,
                        "cycle_length": len(cycle_path) - 1,
                    },
                )
            )
        stack.pop()
        stack_set.remove(node)

    for node in sorted(model_graph):
        if node in visited:
            continue
        dfs(node)
    return diagnostics


def _local_node_id(operation_id: str, local_name: str) -> str:
    return f"local_model:{operation_id}.{local_name}"
