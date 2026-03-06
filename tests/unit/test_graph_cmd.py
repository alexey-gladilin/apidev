import json
from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _write_contract(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _write_shared_model(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "models" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _seed_graph_example(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "common/page_info.yaml",
        """
contract_type: shared_model
name: PageInfo
description: Page metadata
model:
  type: object
  properties:
    total:
      type: integer
      required: true
""",
    )
    _write_contract(
        tmp_path,
        "users/list_users.yaml",
        """
method: GET
path: /v1/users
auth: bearer
summary: List users
description: Returns users list.
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo:
        $ref: common.PageInfo
errors: []
""",
    )
    _write_contract(
        tmp_path,
        "users/search_users.yaml",
        """
method: GET
path: /v1/users/search
auth: bearer
summary: Search users
description: Returns users search result.
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo:
        $ref: common.PageInfo
errors: []
""",
    )


def test_graph_json_output_contains_nodes_and_edges(tmp_path: Path) -> None:
    _seed_graph_example(tmp_path)

    result = runner.invoke(
        app,
        ["graph", "--project-dir", str(tmp_path), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["format"] == "json"
    assert payload["summary"]["nodes"] >= 2
    assert payload["summary"]["edges"] >= 1
    assert any(edge["target"] == "shared_model:common.PageInfo" for edge in payload["edges"])


def test_graph_mermaid_output_contains_graph_header_and_edge(tmp_path: Path) -> None:
    _seed_graph_example(tmp_path)

    result = runner.invoke(
        app,
        ["graph", "--project-dir", str(tmp_path), "--format", "mermaid"],
    )

    assert result.exit_code == 0
    assert result.output.startswith("graph TD")
    assert "shared_model_common_PageInfo" in result.output


def test_graph_text_output_contains_sections(tmp_path: Path) -> None:
    _seed_graph_example(tmp_path)

    result = runner.invoke(
        app,
        ["graph", "--project-dir", str(tmp_path), "--format", "text"],
    )

    assert result.exit_code == 0
    assert "Dependency Graph Summary" in result.output
    assert "Nodes:" in result.output
    assert "Edges:" in result.output


def test_graph_json_output_exposes_direct_and_reverse_dependencies(tmp_path: Path) -> None:
    _seed_graph_example(tmp_path)

    result = runner.invoke(
        app,
        ["graph", "--project-dir", str(tmp_path), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    edge_pairs = {(edge["source"], edge["target"]) for edge in payload["edges"]}
    assert ("operation:users_list_users", "shared_model:common.PageInfo") in edge_pairs
    assert ("operation:users_search_users", "shared_model:common.PageInfo") in edge_pairs

    reverse_sources = {
        edge["source"]
        for edge in payload["edges"]
        if edge["target"] == "shared_model:common.PageInfo"
    }
    assert reverse_sources == {"operation:users_list_users", "operation:users_search_users"}


def test_graph_json_shape_and_mermaid_edge_export_are_explicit(tmp_path: Path) -> None:
    _seed_graph_example(tmp_path)

    json_result = runner.invoke(
        app,
        ["graph", "--project-dir", str(tmp_path), "--format", "json"],
    )
    assert json_result.exit_code == 0
    payload = json.loads(json_result.output)

    assert set(payload.keys()) == {"format", "summary", "nodes", "edges", "unresolved"}
    assert set(payload["summary"].keys()) == {"nodes", "edges", "unresolved"}
    assert payload["format"] == "json"
    assert payload["nodes"]
    assert payload["edges"]
    assert all(set(node.keys()) >= {"id", "kind", "location"} for node in payload["nodes"])
    assert all(
        set(edge.keys()) == {"source", "target", "ref", "location"} for edge in payload["edges"]
    )

    mermaid_result = runner.invoke(
        app,
        ["graph", "--project-dir", str(tmp_path), "--format", "mermaid"],
    )
    assert mermaid_result.exit_code == 0
    assert mermaid_result.output.startswith("graph TD")
    assert (
        'operation_users_list_users -->|"common.PageInfo"| shared_model_common_PageInfo'
        in mermaid_result.output
    )
