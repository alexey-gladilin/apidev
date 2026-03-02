from pathlib import Path
from typing import Any, cast

import pytest

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
        "integration/handler_registry.py",
        "integration/router_factory.py",
        "integration/auth_registry.py",
        "integration/error_mapper.py",
    ]

    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    assert '"method": "POST"' in operation_map.content
    assert '"path": "/v1/items"' in operation_map.content
    assert '"summary": "Create item"' in operation_map.content
    assert '"description": "Creates item"' in operation_map.content
    assert '"response_status": 201' in operation_map.content
    assert '"contract_fingerprint": "' in operation_map.content
    assert '"auth": "bearer"' in operation_map.content
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
    assert '"summary": "Create item"' in router.content
    assert '"description": "Creates item"' in router.content
    assert '"contract_fingerprint": "' in router.content

    request_model = next(
        change for change in plan.changes if change.path.name == "create_item_request.py"
    )
    assert 'summary: str = "Create item"' in request_model.content
    assert 'description: str = "Creates item"' in request_model.content
    assert "contract_fingerprint: str" in request_model.content

    response_model = next(
        change for change in plan.changes if change.path.name == "create_item_response.py"
    )
    assert "SCHEMA_FRAGMENT = " in response_model.content
    assert '"description": "Item identifier"' in response_model.content

    openapi_docs = next(change for change in plan.changes if change.path.name == "openapi_docs.py")
    assert '"summary": str(entry.get("summary", ""))' in openapi_docs.content
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
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    planned_paths = [
        change.path.relative_to(plan.generated_root).as_posix() for change in plan.changes
    ]
    assert "billing_domain/routes/get_invoice.py" in planned_paths
    assert "billing_domain/models/get_invoice_request.py" in planned_paths
    assert "billing_domain/models/get_invoice_response.py" in planned_paths
    assert "billing_domain/models/get_invoice_error.py" in planned_paths

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
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    planned_paths = [
        change.path.relative_to(plan.generated_root).as_posix() for change in plan.changes
    ]
    assert "domain_segment/routes/operation_segment.py" in planned_paths
    assert "domain_segment/models/operation_segment_request.py" in planned_paths
    assert "domain_segment/models/operation_segment_response.py" in planned_paths
    assert "domain_segment/models/operation_segment_error.py" in planned_paths

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
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    generated_root = tmp_path / ".apidev" / "output" / "api"
    stale_b = generated_root / "transport" / "models" / "zzz_stale.py"
    stale_a = generated_root / "transport" / "models" / "aaa_stale.py"
    stale_b.parent.mkdir(parents=True, exist_ok=True)
    stale_b.write_text("# stale-b", encoding="utf-8")
    stale_a.write_text("# stale-a", encoding="utf-8")

    service = _create_diff_service()
    original_glob = service.fs.glob
    flip = False

    def unstable_glob(root: Path, pattern: str) -> list[Path]:
        nonlocal flip
        paths = original_glob(root, pattern)
        if root == generated_root and pattern == "**/*.py":
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
        change.path.relative_to(generated_root).as_posix()
        for change in first.changes
        if change.change_type == "REMOVE"
    ]
    second_removes = [
        change.path.relative_to(generated_root).as_posix()
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
