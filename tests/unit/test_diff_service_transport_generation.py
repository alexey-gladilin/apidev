from pathlib import Path
import ast
from typing import Any, cast

import pytest

from apidev.application.services.diff_service import DiffService
from apidev.core.constants import DEFAULT_INTEGRATION_DIR
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project_config(project_dir: Path) -> None:
    (project_dir / ".apidev" / "contracts").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        """
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[paths]
templates_dir = ".apidev/templates"
""".strip(),
        encoding="utf-8",
    )


def _write_contract(project_dir: Path, relpath: str, body: str) -> None:
    target = project_dir / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _write_shared_model(project_dir: Path, relpath: str, body: str) -> None:
    target = project_dir / ".apidev" / "models" / relpath
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


def _planned_paths_within_root(plan: Any, root: Path) -> list[str]:
    planned_paths: list[str] = []
    for change in plan.changes:
        if change.path.is_relative_to(root):
            planned_paths.append(change.path.relative_to(root).as_posix())
    return planned_paths


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
intent: read
access_pattern: cached
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
intent: write
access_pattern: imperative
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

    generated_paths = _planned_paths_within_root(plan, plan.generated_dir_path)
    assert generated_paths == [
        "operation_map.py",
        "openapi_docs.py",
        "alpha/__init__.py",
        "alpha/routes/__init__.py",
        "alpha/models/__init__.py",
        "zeta/__init__.py",
        "zeta/routes/__init__.py",
        "zeta/models/__init__.py",
        "alpha/routes/create_item.py",
        "alpha/models/create_item_request.py",
        "alpha/models/create_item_response.py",
        "alpha/models/create_item_error.py",
        "zeta/routes/get_status.py",
        "zeta/models/get_status_request.py",
        "zeta/models/get_status_response.py",
        "zeta/models/get_status_error.py",
    ]
    scaffold_paths = _planned_paths_within_root(plan, tmp_path / DEFAULT_INTEGRATION_DIR)
    assert scaffold_paths == [
        "handler_registry.py",
        "router_factory.py",
        "auth_registry.py",
        "error_mapper.py",
    ]

    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    assert '"method": "POST"' in operation_map.content
    assert '"path": "/v1/items"' in operation_map.content
    assert '"description": "Creates item"' in operation_map.content
    assert '"response_status": 201' in operation_map.content
    assert '"contract_fingerprint": "' in operation_map.content
    assert '"auth": "bearer"' in operation_map.content
    assert '"intent": "write"' in operation_map.content
    assert '"access_pattern": "imperative"' in operation_map.content
    assert '"router_module": "alpha.routes.create_item"' in operation_map.content
    assert (
        '"request": "alpha.models.create_item_request.AlphaCreateItemRequest"'
        in operation_map.content
    )
    assert (
        '"response": "alpha.models.create_item_response.AlphaCreateItemResponse"'
        in operation_map.content
    )
    assert '"error": "alpha.models.create_item_error.AlphaCreateItemError"' in operation_map.content
    assert '"callable": "alpha.routes.create_item.route"' in operation_map.content

    router = next(change for change in plan.changes if change.path.name == "create_item.py")
    assert '"description": "Creates item"' in router.content
    assert '"contract_fingerprint": "' in router.content

    request_model = next(
        change for change in plan.changes if change.path.name == "create_item_request.py"
    )
    assert 'description: str = "Creates item"' in request_model.content
    assert "contract_fingerprint: str" in request_model.content

    response_model = next(
        change for change in plan.changes if change.path.name == "create_item_response.py"
    )
    assert "SCHEMA_FRAGMENT = " in response_model.content
    assert '"description": "Item identifier"' in response_model.content

    openapi_docs = next(change for change in plan.changes if change.path.name == "openapi_docs.py")
    assert '"description": str(entry.get("description", ""))' in openapi_docs.content
    assert 'response_status = str(int(entry.get("response_status", 200)))' in openapi_docs.content
    assert "response_status: {" in openapi_docs.content


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
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
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


def test_diff_service_request_model_schema_fragment_snapshot(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
  query:
    type: object
    properties:
      include_payments:
        type: boolean
  body:
    type: object
    properties:
      trace_id:
        type: string
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    request_model = next(
        change for change in plan.changes if change.path.name == "get_invoice_request.py"
    )

    expected_fragment = {
        "body": {"properties": {"trace_id": {"type": "string"}}, "type": "object"},
        "path": {"properties": {"invoice_id": {"type": "string"}}, "type": "object"},
        "query": {
            "properties": {"include_payments": {"type": "boolean"}},
            "type": "object",
        },
    }
    fragment_source = (
        request_model.content.split("SCHEMA_FRAGMENT = ", 1)[1]
        .split("\nSCHEMA_EXAMPLE", 1)[0]
        .strip()
    )
    request_model_fragment = ast.literal_eval(fragment_source)
    assert request_model_fragment == expected_fragment


def test_diff_service_normalizes_single_level_domain_and_operation_segments(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "Billing-Domain/Get Invoice!.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    generated_paths = _planned_paths_within_root(plan, plan.generated_dir_path)
    assert "billing_domain/routes/get_invoice.py" in generated_paths
    assert "billing_domain/models/get_invoice_request.py" in generated_paths
    assert "billing_domain/models/get_invoice_response.py" in generated_paths
    assert "billing_domain/models/get_invoice_error.py" in generated_paths

    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    assert '"router_module": "billing_domain.routes.get_invoice"' in operation_map.content
    assert (
        '"request": "billing_domain.models.get_invoice_request.BillingDomainGetInvoiceRequest"'
        in operation_map.content
    )


def test_diff_service_rejects_nested_contract_paths_for_single_level_layout(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/invoices/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    with pytest.raises(ValueError, match="single-level"):
        _create_diff_service().run(tmp_path)


def test_diff_service_fails_fast_on_normalized_transport_path_collision(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get-invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice A
description: Get invoice A
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
response:
  status: 200
  body:
    type: object
errors: []
""",
    )
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice B
description: Get invoice B
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    with pytest.raises(ValueError, match="collision"):
        _create_diff_service().run(tmp_path)


def test_diff_service_normalizes_empty_segments_to_deterministic_fallback_names(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "!/!.yaml",
        """
method: GET
path: /v1/fallback
auth: bearer
summary: Fallback names
description: Fallback names
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    generated_paths = _planned_paths_within_root(plan, plan.generated_dir_path)
    assert "domain_segment/routes/operation_segment.py" in generated_paths
    assert "domain_segment/models/operation_segment_request.py" in generated_paths
    assert "domain_segment/models/operation_segment_response.py" in generated_paths
    assert "domain_segment/models/operation_segment_error.py" in generated_paths

    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    assert '"router_module": "domain_segment.routes.operation_segment"' in operation_map.content
    assert '"request": "domain_segment.models.operation_segment_request.OperationRequest"' in (
        operation_map.content
    )


def test_diff_service_collision_diagnostic_is_deterministic_for_empty_normalized_segments(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "!/!.yaml",
        """
method: GET
path: /v1/fallback-a
auth: bearer
summary: Fallback A
description: Fallback A
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
errors: []
""",
    )
    _write_contract(
        tmp_path,
        "??/??.yaml",
        """
method: GET
path: /v1/fallback-b
auth: bearer
summary: Fallback B
description: Fallback B
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    with pytest.raises(ValueError, match="Normalized transport path collision detected") as exc:
        _create_diff_service().run(tmp_path)

    message = str(exc.value)
    assert "target=domain_segment/operation_segment" in message
    assert "contracts=!/!.yaml,??/??.yaml" in message


def test_diff_service_remove_plan_is_deterministic_with_unstable_glob(tmp_path: Path) -> None:
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
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    stale_b = generated_dir_path / "transport" / "models" / "zzz_stale.py"
    stale_a = generated_dir_path / "transport" / "models" / "aaa_stale.py"
    stale_b.parent.mkdir(parents=True, exist_ok=True)
    stale_b.write_text("# stale-b", encoding="utf-8")
    stale_a.write_text("# stale-a", encoding="utf-8")

    service = _create_diff_service()
    original_glob = service.fs.glob
    flip = False

    def unstable_glob(root: Path, pattern: str) -> list[Path]:
        nonlocal flip
        paths = original_glob(root, pattern)
        if root == generated_dir_path and pattern == "**/*.py":
            stale_paths = [path for path in paths if path.name in {"aaa_stale.py", "zzz_stale.py"}]
            stable_paths = [path for path in paths if path not in stale_paths]
            flip = not flip
            ordered_stale = list(reversed(stale_paths)) if flip else stale_paths
            return stable_paths + ordered_stale + ordered_stale[:1]
        return paths

    service.fs.glob = unstable_glob  # type: ignore[method-assign]

    first = service.run(tmp_path)
    second = service.run(tmp_path)

    first_removes = [
        change.path.relative_to(generated_dir_path).as_posix()
        for change in first.changes
        if change.change_type == "REMOVE"
    ]
    second_removes = [
        change.path.relative_to(generated_dir_path).as_posix()
        for change in second.changes
        if change.change_type == "REMOVE"
    ]
    assert first_removes == [
        "transport/models/aaa_stale.py",
        "transport/models/zzz_stale.py",
    ]
    assert second_removes == first_removes


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
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
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
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
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


def test_diff_service_normalizes_short_form_error_example_for_projection(tmp_path: Path) -> None:
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
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
response:
  status: 200
  body:
    type: object
errors:
  - code: INVOICE_NOT_FOUND
    http_status: 404
    example:
      code: INVOICE_NOT_FOUND
      message: Invoice not found
    body:
      type: object
      properties:
        code:
          type: string
          required: true
        message:
          type: string
""".strip(),
        encoding="utf-8",
    )

    plan = _create_diff_service().run(tmp_path)
    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    namespace: dict[str, object] = {}
    exec(operation_map.content, {}, namespace)
    operation_map_value = cast(dict[str, Any], namespace["OPERATION_MAP"])
    entry = operation_map_value["billing_get_invoice"]

    assert entry["error_examples"] == [
        {"code": "INVOICE_NOT_FOUND", "message": "Invoice not found"}
    ]


def test_diff_service_rejects_malicious_path_literal_for_codegen_safety(
    tmp_path: Path,
) -> None:
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
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    with pytest.raises(
        ValueError,
        match=(
            r"Invalid contract at billing/get_invoice\.yaml: "
            r"Field 'path' contains unsupported characters for code generation safety\.; "
            r"Field 'path' must contain only URL-safe characters and parameter braces\."
        ),
    ):
        _create_diff_service().run(tmp_path)


def test_operation_map_includes_domain_for_runtime_and_openapi_projection(tmp_path: Path) -> None:
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
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
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
    operation_map_value = cast(dict[str, Any], namespace["OPERATION_MAP"])
    entry = operation_map_value["billing_get_invoice"]

    assert entry["domain"] == "billing"


def test_operation_map_publishes_operation_semantics_metadata(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
intent: read
access_pattern: both
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
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
    operation_map_value = cast(dict[str, Any], namespace["OPERATION_MAP"])
    entry = operation_map_value["billing_get_invoice"]

    assert entry["intent"] == "read"
    assert entry["access_pattern"] == "both"


def test_operation_map_publishes_consistent_request_metadata_contract(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
  query:
    type: object
    properties:
      expand:
        type: boolean
  body:
    type: object
    properties:
      include_history:
        type: boolean
response:
  status: 200
  body:
    type: object
errors: []
""",
    )
    _write_contract(
        tmp_path,
        "zeta/get_status.yaml",
        """
method: GET
path: /v1/status
auth: public
summary: Get status
description: Returns status
intent: read
access_pattern: cached
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
    operation_map_value = cast(dict[str, dict[str, object]], namespace["OPERATION_MAP"])

    for entry in operation_map_value.values():
        assert "request" in entry
        request_metadata = cast(dict[str, object], entry["request"])
        assert set(request_metadata.keys()) == {"path", "query", "body"}
        assert isinstance(request_metadata["path"], dict)
        assert isinstance(request_metadata["query"], dict)
        assert isinstance(request_metadata["body"], dict)

    billing_entry = operation_map_value["billing_get_invoice"]
    assert billing_entry["request"] == {
        "path": {
            "properties": {"invoice_id": {"type": "string"}},
            "type": "object",
        },
        "query": {
            "properties": {"expand": {"type": "boolean"}},
            "type": "object",
        },
        "body": {
            "properties": {"include_history": {"type": "boolean"}},
            "type": "object",
        },
    }

    legacy_entry = operation_map_value["zeta_get_status"]
    assert legacy_entry["request"] == {
        "path": {},
        "query": {},
        "body": {},
    }


def test_openapi_projection_includes_domain_tags_security_and_error_responses(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
response:
  status: 200
  body:
    type: object
errors:
  - code: INVOICE_NOT_FOUND
    http_status: 404
    body:
      type: object
      example:
        code: INVOICE_NOT_FOUND
""",
    )

    plan = _create_diff_service().run(tmp_path)
    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    openapi_docs = next(change for change in plan.changes if change.path.name == "openapi_docs.py")

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map.content, {}, operation_map_namespace)
    operation_map_value = operation_map_namespace["OPERATION_MAP"]

    openapi_source = openapi_docs.content.replace(
        "from .operation_map import OPERATION_MAP\n\n", ""
    )
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = build_openapi_paths()
    get_operation = paths["/v1/invoices/{invoice_id}"]["get"]

    assert get_operation["tags"] == ["billing"]
    assert get_operation["security"] == [{"bearerAuth": []}]
    assert "200" in get_operation["responses"]
    assert "404" in get_operation["responses"]


def test_openapi_projection_builds_parameters_and_request_body_from_request_metadata(
    tmp_path: Path,
) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/update_invoice.yaml",
        """
method: POST
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Update invoice
description: Update invoice details
intent: write
access_pattern: imperative
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
  query:
    type: object
    properties:
      expand:
        type: boolean
        required: true
      locale:
        type: string
  body:
    type: object
    properties:
      include_history:
        type: boolean
response:
  status: 200
  body:
    type: object
errors: []
""",
    )
    _write_contract(
        tmp_path,
        "zeta/get_status.yaml",
        """
method: GET
path: /v1/status
auth: public
summary: Get status
description: Returns status
intent: read
access_pattern: cached
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
    openapi_docs = next(change for change in plan.changes if change.path.name == "openapi_docs.py")

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map.content, {}, operation_map_namespace)
    operation_map_value = cast(
        dict[str, dict[str, object]], operation_map_namespace["OPERATION_MAP"]
    )

    openapi_source = openapi_docs.content.replace(
        "from .operation_map import OPERATION_MAP\n\n", ""
    )
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = cast(dict[str, dict[str, dict[str, object]]], build_openapi_paths())

    post_operation = paths["/v1/invoices/{invoice_id}"]["post"]
    assert post_operation["parameters"] == [
        {
            "in": "path",
            "name": "invoice_id",
            "required": True,
            "schema": {"type": "string"},
        },
        {
            "in": "query",
            "name": "expand",
            "required": True,
            "schema": {"required": True, "type": "boolean"},
        },
        {
            "in": "query",
            "name": "locale",
            "required": False,
            "schema": {"type": "string"},
        },
    ]
    assert post_operation["requestBody"] == {
        "content": {
            "application/json": {
                "schema": {
                    "properties": {"include_history": {"type": "boolean"}},
                    "type": "object",
                }
            }
        }
    }

    get_operation = paths["/v1/status"]["get"]
    assert "parameters" not in get_operation
    assert "requestBody" not in get_operation


def test_openapi_projection_emits_components_for_shared_model_refs(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_shared_model(
        tmp_path,
        "common/pagination_request.yaml",
        """
contract_type: shared_model
name: PaginationRequest
description: Shared pagination payload
model:
  type: object
  properties:
    number:
      type: integer
      required: true
    size:
      type: integer
      required: true
""",
    )
    _write_contract(
        tmp_path,
        "billing/search_invoices.yaml",
        """
method: POST
path: /v1/invoices/search
auth: bearer
summary: Search invoices
description: Search invoices with shared pagination
intent: read
access_pattern: cached
request:
  body:
    type: object
    properties:
      page:
        $ref: common.PaginationRequest
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
    openapi_docs = next(change for change in plan.changes if change.path.name == "openapi_docs.py")

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map.content, {}, operation_map_namespace)
    operation_map_value = cast(
        dict[str, dict[str, object]], operation_map_namespace["OPERATION_MAP"]
    )

    openapi_source = openapi_docs.content.replace(
        "from .operation_map import OPERATION_MAP\n\n", ""
    )
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    build_openapi_components = cast(Any, openapi_namespace["build_openapi_components"])

    paths = cast(dict[str, dict[str, dict[str, object]]], build_openapi_paths())
    components = cast(dict[str, dict[str, object]], build_openapi_components())

    search_operation = cast(dict[str, object], paths["/v1/invoices/search"]["post"])
    search_request_body = cast(dict[str, object], search_operation["requestBody"])
    search_request_content = cast(dict[str, object], search_request_body["content"])
    request_body_content = cast(dict[str, object], search_request_content["application/json"])
    request_body_schema = cast(dict[str, object], request_body_content["schema"])
    assert request_body_schema == {
        "type": "object",
        "properties": {
            "page": {"$ref": "#/components/schemas/common.PaginationRequest"},
        },
    }
    assert components == {
        "common.PaginationRequest": {
            "type": "object",
            "properties": {
                "number": {"type": "integer", "required": True},
                "size": {"type": "integer", "required": True},
            },
        }
    }


def test_operation_map_normalizes_response_and_error_shared_model_refs(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_shared_model(
        tmp_path,
        "common/page_info.yaml",
        """
contract_type: shared_model
name: PageInfo
description: Shared page info
model:
  type: object
  properties:
    total:
      type: integer
      required: true
""",
    )
    _write_shared_model(
        tmp_path,
        "common/api_error.yaml",
        """
contract_type: shared_model
name: ApiError
description: Shared API error
model:
  type: object
  properties:
    message:
      type: string
      required: true
""",
    )
    _write_contract(
        tmp_path,
        "billing/search_invoices.yaml",
        """
method: POST
path: /v1/invoices/search
auth: bearer
summary: Search invoices
description: Search invoices with shared refs
intent: read
access_pattern: cached
request:
  body:
    type: object
response:
  status: 200
  body:
    type: object
    properties:
      page:
        $ref: common.PageInfo
errors:
  - code: BAD_REQUEST
    http_status: 400
    body:
      $ref: common.ApiError
""",
    )

    plan = _create_diff_service().run(tmp_path)
    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map.content, {}, operation_map_namespace)
    operation_map_value = cast(
        dict[str, dict[str, object]], operation_map_namespace["OPERATION_MAP"]
    )
    search_entry = cast(dict[str, object], operation_map_value["billing_search_invoices"])
    response_schema = cast(dict[str, object], search_entry["response_schema"])
    response_properties = cast(dict[str, object], response_schema["properties"])
    page_schema = cast(dict[str, object], response_properties["page"])
    error_schemas = cast(list[dict[str, object]], search_entry["error_schemas"])
    error_body = cast(dict[str, object], error_schemas[0]["body"])

    assert page_schema["$ref"] == "#/components/schemas/common.PageInfo"
    assert error_body["$ref"] == "#/components/schemas/common.ApiError"
