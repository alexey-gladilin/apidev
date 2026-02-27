from pathlib import Path
from typing import Any, cast

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project_config(project_dir: Path) -> None:
    (project_dir / ".apidev" / "contracts").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"
""".strip(),
        encoding="utf-8",
    )


def _write_contract(project_dir: Path, relpath: str, body: str) -> None:
    target = project_dir / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _create_diff_service() -> DiffService:
    fs = LocalFileSystem()
    return DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )


def test_diff_service_generates_transport_models_and_registry_metadata(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "zeta/get_status.yaml",
        """
method: GET
path: /v1/status
auth: public
summary: Get status
description: Returns status
response:
  status: 200
  body:
    type: object
errors:
  - code: SERVICE_UNAVAILABLE
    http_status: 503
    body:
      type: object
""",
    )
    _write_contract(
        tmp_path,
        "alpha/create_item.yaml",
        """
method: POST
path: /v1/items
auth: bearer
summary: Create item
description: Creates item
response:
  status: 201
  body:
    type: object
    properties:
      item_id:
        type: string
        description: Item identifier
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)

    planned_paths = [
        change.path.relative_to(plan.generated_root).as_posix() for change in plan.changes
    ]
    assert planned_paths == [
        "operation_map.py",
        "openapi_docs.py",
        "routers/alpha_create_item.py",
        "transport/models/alpha_create_item_request.py",
        "transport/models/alpha_create_item_response.py",
        "transport/models/alpha_create_item_error.py",
        "routers/zeta_get_status.py",
        "transport/models/zeta_get_status_request.py",
        "transport/models/zeta_get_status_response.py",
        "transport/models/zeta_get_status_error.py",
    ]

    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    assert '"method": "POST"' in operation_map.content
    assert '"path": "/v1/items"' in operation_map.content
    assert '"summary": "Create item"' in operation_map.content
    assert '"description": "Creates item"' in operation_map.content
    assert '"contract_fingerprint": "' in operation_map.content
    assert '"router_module": "routers.alpha_create_item"' in operation_map.content
    assert (
        '"request": "transport.models.alpha_create_item_request.AlphaCreateItemRequest"'
        in operation_map.content
    )
    assert (
        '"response": "transport.models.alpha_create_item_response.AlphaCreateItemResponse"'
        in operation_map.content
    )
    assert (
        '"error": "transport.models.alpha_create_item_error.AlphaCreateItemError"'
        in operation_map.content
    )
    assert '"callable": "routers.alpha_create_item.route"' in operation_map.content

    router = next(change for change in plan.changes if change.path.name == "alpha_create_item.py")
    assert '"summary": "Create item"' in router.content
    assert '"description": "Creates item"' in router.content
    assert '"contract_fingerprint": "' in router.content

    request_model = next(
        change for change in plan.changes if change.path.name == "alpha_create_item_request.py"
    )
    assert 'summary: str = "Create item"' in request_model.content
    assert 'description: str = "Creates item"' in request_model.content
    assert "contract_fingerprint: str" in request_model.content

    response_model = next(
        change for change in plan.changes if change.path.name == "alpha_create_item_response.py"
    )
    assert "SCHEMA_FRAGMENT = " in response_model.content
    assert '"description": "Item identifier"' in response_model.content

    openapi_docs = next(change for change in plan.changes if change.path.name == "openapi_docs.py")
    assert '"summary": str(entry.get("summary", ""))' in openapi_docs.content
    assert '"description": str(entry.get("description", ""))' in openapi_docs.content


def test_diff_service_transport_generation_is_deterministic(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    service = _create_diff_service()
    first = service.run(tmp_path)
    second = service.run(tmp_path)

    first_snapshot = [(change.path.as_posix(), change.content) for change in first.changes]
    second_snapshot = [(change.path.as_posix(), change.content) for change in second.changes]
    assert first_snapshot == second_snapshot


def test_diff_service_propagates_examples_into_metadata_and_fingerprint(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body:
    type: object
    example:
      invoice_id: inv-001
errors:
  - code: INVOICE_NOT_FOUND
    http_status: 404
    body:
      type: object
      example:
        code: INVOICE_NOT_FOUND
""".strip(),
        encoding="utf-8",
    )

    first_plan = _create_diff_service().run(tmp_path)
    first_operation_map = next(
        change for change in first_plan.changes if change.path.name == "operation_map.py"
    )
    first_namespace: dict[str, object] = {}
    exec(first_operation_map.content, {}, first_namespace)
    first_operation_map_value = cast(dict[str, Any], first_namespace["OPERATION_MAP"])
    first_entry = first_operation_map_value["billing_get_invoice"]

    assert first_entry["response_example"] == {"invoice_id": "inv-001"}
    assert first_entry["error_examples"] == [{"code": "INVOICE_NOT_FOUND"}]

    first_fingerprint = first_entry["contract_fingerprint"]
    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body:
    type: object
    example:
      invoice_id: inv-002
errors:
  - code: INVOICE_NOT_FOUND
    http_status: 404
    body:
      type: object
      example:
        code: INVOICE_NOT_FOUND
""".strip(),
        encoding="utf-8",
    )

    second_plan = _create_diff_service().run(tmp_path)
    second_operation_map = next(
        change for change in second_plan.changes if change.path.name == "operation_map.py"
    )
    second_namespace: dict[str, object] = {}
    exec(second_operation_map.content, {}, second_namespace)
    second_operation_map_value = cast(dict[str, Any], second_namespace["OPERATION_MAP"])
    second_entry = second_operation_map_value["billing_get_invoice"]

    assert second_entry["response_example"] == {"invoice_id": "inv-002"}
    assert first_fingerprint != second_entry["contract_fingerprint"]


def test_operation_map_escapes_malicious_path_literal(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    malicious_path = '/x"+__import__("os").system("echo_INJECTED")+"'
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        f"""
method: GET
path: '{malicious_path}'
auth: bearer
summary: Get invoice
description: Get invoice
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )

    namespace: dict[str, object] = {}
    exec(operation_map.content, {}, namespace)
    operation_map_value = namespace["OPERATION_MAP"]
    assert isinstance(operation_map_value, dict)
    assert operation_map_value["billing_get_invoice"]["path"] == malicious_path
