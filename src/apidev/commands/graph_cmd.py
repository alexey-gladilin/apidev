import json
import re
from pathlib import Path
from typing import Literal

import typer

from apidev.commands.runtime import load_runtime
from apidev.core.models.operation import Operation
from apidev.core.rules.contract_schema import validate_contract_schema
from apidev.core.rules.contract_semantic import build_dependency_graph, validate_semantic_rules
from apidev.core.rules.operation_id import build_operation_id
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader


def _safe_mermaid_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def _render_text_graph(payload: dict[str, list[dict[str, str]]]) -> str:
    nodes = payload["nodes"]
    edges = payload["edges"]
    unresolved = payload["unresolved"]
    lines: list[str] = [
        "Dependency Graph Summary",
        f"Nodes: {len(nodes)}",
        f"Edges: {len(edges)}",
        f"Unresolved: {len(unresolved)}",
        "",
        "Edges:",
    ]
    if not edges:
        lines.append("- (none)")
    else:
        for edge in edges:
            lines.append(f"- {edge['source']} -> {edge['target']} (ref={edge['ref']})")

    lines.append("")
    lines.append("Unresolved:")
    if not unresolved:
        lines.append("- (none)")
    else:
        for item in unresolved:
            lines.append(f"- {item['source']} -> {item['ref']} ({item['reason']})")
    return "\n".join(lines)


def _render_mermaid_graph(payload: dict[str, list[dict[str, str]]]) -> str:
    lines: list[str] = ["graph TD"]
    nodes_by_id = {node["id"]: node for node in payload["nodes"]}
    for node_id in sorted(nodes_by_id):
        node = nodes_by_id[node_id]
        lines.append(f'    {_safe_mermaid_id(node_id)}["{node_id} ({node["kind"]})"]')
    for edge in payload["edges"]:
        source_id = _safe_mermaid_id(edge["source"])
        target_id = _safe_mermaid_id(edge["target"])
        lines.append(f'    {source_id} -->|"{edge["ref"]}"| {target_id}')
    return "\n".join(lines)


def _load_validated_operations(
    *,
    operation_documents: list,
    shared_model_documents: list,
) -> list[Operation]:
    operations: list[Operation] = []
    schema_errors = False
    for document in operation_documents:
        contract, diagnostics = validate_contract_schema(document)
        if diagnostics:
            schema_errors = True
        if contract is None:
            continue
        operations.append(
            Operation(
                operation_id=build_operation_id(document.contract_relpath.as_posix()),
                contract=contract,
                contract_relpath=document.contract_relpath,
            )
        )

    for document in shared_model_documents:
        _, diagnostics = validate_contract_schema(document)
        if diagnostics:
            schema_errors = True

    semantic_diagnostics = validate_semantic_rules(
        operations,
        operation_documents=operation_documents,
        shared_model_documents=shared_model_documents,
    )
    if schema_errors or semantic_diagnostics:
        typer.echo("Validation failed. Run `apidev validate` for details.")
        raise SystemExit(1)

    return operations


def graph_command(
    project_dir: Path = Path("."),
    output_format: Literal["text", "json", "mermaid"] = typer.Option(
        "text",
        "--format",
        help="Graph output format.",
    ),
) -> None:
    _, paths = load_runtime(project_dir.resolve())
    loader = YamlContractLoader()
    operation_documents = loader.load_documents(paths.contracts_dir)
    shared_model_documents = loader.load_documents(paths.shared_models_dir)
    operations = _load_validated_operations(
        operation_documents=operation_documents,
        shared_model_documents=shared_model_documents,
    )

    payload = build_dependency_graph(
        operations=operations,
        operation_documents=operation_documents,
        shared_model_documents=shared_model_documents,
    )
    if output_format == "json":
        body = {
            "format": "json",
            "summary": {
                "nodes": len(payload["nodes"]),
                "edges": len(payload["edges"]),
                "unresolved": len(payload["unresolved"]),
            },
            "nodes": payload["nodes"],
            "edges": payload["edges"],
            "unresolved": payload["unresolved"],
        }
        typer.echo(json.dumps(body, ensure_ascii=False))
        return
    if output_format == "mermaid":
        typer.echo(_render_mermaid_graph(payload))
        return
    typer.echo(_render_text_graph(payload))
