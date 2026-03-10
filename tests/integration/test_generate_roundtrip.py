import json
import importlib
import ast
from pathlib import Path
import sys
from typing import Any, cast

import pytest

from apidev.application.dto.generation_plan import EndpointFilters
from apidev.application.services.generate_service import GenerateService
from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.output.writer import SafeWriter
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def test_generate_idempotent(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text("""
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[paths]
templates_dir = ".apidev/templates"
""".strip())
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text("""
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
  body: {type: object}
errors: []
""".strip())

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    first = service.run(tmp_path, baseline_ref="v1.0.0")
    second = service.run(tmp_path, baseline_ref="v1.0.0")

    assert first.applied_changes >= 1
    assert second.applied_changes == 0


def test_generate_creates_runnable_transport_skeleton(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
    properties:
      invoice_id:
        type: string
        description: Invoice identifier
errors:
  - code: INVOICE_NOT_FOUND
    http_status: 404
    body: {type: object}
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    result = service.run(tmp_path, baseline_ref="v1.0.0")

    assert result.applied_changes >= 5
    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    router = generated_dir_path / "billing" / "routes" / "get_invoice.py"
    openapi_docs = generated_dir_path / "openapi_docs.py"
    request_model = generated_dir_path / "billing" / "models" / "get_invoice_request.py"
    response_model = generated_dir_path / "billing" / "models" / "get_invoice_response.py"
    error_model = generated_dir_path / "billing" / "models" / "get_invoice_error.py"

    assert router.exists()
    assert openapi_docs.exists()
    assert request_model.exists()
    assert response_model.exists()
    assert error_model.exists()

    compile(router.read_text(encoding="utf-8"), str(router), "exec")
    compile(openapi_docs.read_text(encoding="utf-8"), str(openapi_docs), "exec")
    compile(request_model.read_text(encoding="utf-8"), str(request_model), "exec")
    compile(response_model.read_text(encoding="utf-8"), str(response_model), "exec")
    compile(error_model.read_text(encoding="utf-8"), str(error_model), "exec")
    assert '"description": "Invoice identifier"' in response_model.read_text(encoding="utf-8")


def test_generate_request_model_schema_snapshot_from_request_fragments(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
        type: string
  body:
    type: object
    properties:
      comment:
        type: string
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")
    request_model = (
        tmp_path / ".apidev" / "output" / "api" / "billing" / "models" / "get_invoice_request.py"
    )
    content = request_model.read_text(encoding="utf-8")

    expected_fragment = {
        "body": {"properties": {"comment": {"type": "string"}}, "type": "object"},
        "path": {"properties": {"invoice_id": {"type": "string"}}, "type": "object"},
        "query": {"properties": {"expand": {"type": "string"}}, "type": "object"},
    }
    fragment_source = (
        content.split("SCHEMA_FRAGMENT = ", 1)[1].split("\nSCHEMA_EXAMPLE", 1)[0].strip()
    )
    actual_fragment = ast.literal_eval(fragment_source)
    assert actual_fragment == expected_fragment


def test_generate_legacy_contract_without_request_keeps_projection_backwards_compatible(
    tmp_path: Path,
) -> None:
    (tmp_path / ".apidev" / "contracts" / "zeta").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "zeta" / "get_status.yaml").write_text(
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
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_source = (generated_dir_path / "operation_map.py").read_text(encoding="utf-8")
    request_model_source = (
        generated_dir_path / "zeta" / "models" / "get_status_request.py"
    ).read_text(encoding="utf-8")
    openapi_docs_source = (generated_dir_path / "openapi_docs.py").read_text(encoding="utf-8")

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_source, {}, operation_map_namespace)
    operation_map_value = cast(
        dict[str, dict[str, object]], operation_map_namespace["OPERATION_MAP"]
    )
    assert operation_map_value["zeta_get_status"]["request"] == {
        "path": {},
        "query": {},
        "body": {},
    }
    assert "SCHEMA_FRAGMENT = {}" in request_model_source

    openapi_source = openapi_docs_source.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = cast(dict[str, dict[str, dict[str, object]]], build_openapi_paths())
    get_operation = paths["/v1/status"]["get"]

    assert "parameters" not in get_operation
    assert "requestBody" not in get_operation


def test_generate_openapi_request_projection_snapshot_from_request_metadata(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "contracts" / "zeta").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "update_invoice.yaml").write_text(
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
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".apidev" / "contracts" / "zeta" / "get_status.yaml").write_text(
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
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_source = (generated_dir_path / "operation_map.py").read_text(encoding="utf-8")
    openapi_docs_source = (generated_dir_path / "openapi_docs.py").read_text(encoding="utf-8")

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_source, {}, operation_map_namespace)
    operation_map_value = cast(
        dict[str, dict[str, object]], operation_map_namespace["OPERATION_MAP"]
    )

    openapi_source = openapi_docs_source.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = cast(dict[str, dict[str, dict[str, object]]], build_openapi_paths())

    expected_post_operation = {
        "operationId": "billing_update_invoice",
        "description": "Update invoice details",
        "deprecated": False,
        "tags": ["billing"],
        "responses": {
            "200": {
                "description": "Success",
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                        "example": None,
                    }
                },
            }
        },
        "x-apidev-auth": "bearer",
        "x-apidev-deprecation": {
            "status": "active",
            "deprecated_since_release": None,
        },
        "x-apidev-errors": [],
        "security": [{"bearerAuth": []}],
        "parameters": [
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
        ],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {"include_history": {"type": "boolean"}},
                        "type": "object",
                    }
                }
            }
        },
    }
    assert paths["/v1/invoices/{invoice_id}"]["post"] == expected_post_operation

    expected_get_operation = {
        "operationId": "zeta_get_status",
        "description": "Returns status",
        "deprecated": False,
        "tags": ["zeta"],
        "responses": {
            "200": {
                "description": "Success",
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                        "example": None,
                    }
                },
            }
        },
        "x-apidev-auth": "public",
        "x-apidev-deprecation": {
            "status": "active",
            "deprecated_since_release": None,
        },
        "x-apidev-errors": [],
    }
    assert paths["/v1/status"]["get"] == expected_get_operation


def test_generate_creates_domain_package_markers_and_runtime_imports(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    assert (generated_dir_path / "billing" / "__init__.py").exists()
    assert (generated_dir_path / "billing" / "routes" / "__init__.py").exists()
    assert (generated_dir_path / "billing" / "models" / "__init__.py").exists()

    inserted = str(generated_dir_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    try:
        operation_map_module = importlib.import_module("operation_map")
        loaded_modules.append("operation_map")
        operation_map = cast(dict[str, Any], operation_map_module.OPERATION_MAP)
        entry = cast(dict[str, Any], operation_map["billing_get_invoice"])

        router_module_name = str(entry["router_module"])
        importlib.import_module(router_module_name)
        loaded_modules.append(router_module_name)

        callable_path = str(cast(dict[str, Any], entry["bridge"])["callable"])
        callable_module_name, callable_attr = callable_path.rsplit(".", 1)
        callable_module = importlib.import_module(callable_module_name)
        loaded_modules.append(callable_module_name)
        route_callable = getattr(callable_module, callable_attr)
        assert callable(route_callable)
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_generate_check_detects_drift_for_changed_contract(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    no_drift = service.run(tmp_path, check=True)
    assert not no_drift.drift_detected
    assert no_drift.drift_status == "no-drift"

    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}/details
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    drift = service.run(tmp_path, check=True)
    assert drift.drift_detected
    assert drift.drift_status == "drift"


def test_generate_check_detects_drift_for_changed_description(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    no_drift = service.run(tmp_path, check=True)
    assert not no_drift.drift_detected
    assert no_drift.drift_status == "no-drift"

    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Updated description for swagger
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    drift = service.run(tmp_path, check=True)
    assert drift.drift_detected
    assert drift.drift_status == "drift"


def test_generate_apply_removes_stale_generated_artifact_and_reports_no_drift(
    tmp_path: Path,
) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")
    stale_file = tmp_path / ".apidev" / "output" / "api" / "routers" / "obsolete_route.py"
    stale_file.parent.mkdir(parents=True, exist_ok=True)
    stale_file.write_text("# stale\n", encoding="utf-8")

    check_result = service.run(tmp_path, check=True)
    assert check_result.drift_status == "drift"

    apply_result = service.run(tmp_path, baseline_ref="v1.0.0")

    assert not stale_file.exists()
    assert apply_result.drift_status == "no-drift"
    assert apply_result.applied_changes >= 1


def test_generate_apply_maps_remove_failure_to_error_status(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")
    stale_file = tmp_path / ".apidev" / "output" / "api" / "routers" / "obsolete_route.py"
    stale_file.parent.mkdir(parents=True, exist_ok=True)
    stale_file.write_text("# stale\n", encoding="utf-8")

    def _raise_remove_error(generated_dir_path: Path, target: Path) -> bool:
        raise ValueError(f"remove failed for {target}")

    monkeypatch.setattr(service, "_remove_generated_artifact", _raise_remove_error)

    result = service.run(tmp_path, baseline_ref="v1.0.0")

    assert result.drift_status == "error"


def test_generate_remove_contract_roundtrip_diff_check_gen_ends_without_drift(
    tmp_path: Path,
) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    config_loader = TomlConfigLoader(fs=fs)
    loader = YamlContractLoader()
    renderer = JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates")
    postprocessor = PythonPostprocessor()
    service = GenerateService(
        config_loader=config_loader,
        loader=loader,
        renderer=renderer,
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=postprocessor,
    )
    diff_service = DiffService(
        config_loader=config_loader,
        loader=loader,
        renderer=renderer,
        fs=fs,
        postprocessor=postprocessor,
    )

    first_apply = service.run(tmp_path, baseline_ref="v1.0.0")
    assert first_apply.applied_changes >= 1
    assert first_apply.drift_status == "no-drift"

    contract_path.unlink()

    diff_plan = diff_service.run(tmp_path)
    diff_changes = [c for c in diff_plan.changes if c.change_type in {"ADD", "UPDATE", "REMOVE"}]
    assert any(change.change_type == "REMOVE" for change in diff_changes)

    drift_check = service.run(tmp_path, check=True)
    assert drift_check.drift_status == "drift"
    assert drift_check.drift_detected

    apply_remove = service.run(tmp_path, baseline_ref="v1.0.0")
    assert apply_remove.drift_status == "no-drift"
    assert apply_remove.applied_changes >= 1

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    assert not (generated_dir_path / "billing" / "routes" / "get_invoice.py").exists()
    assert not (generated_dir_path / "billing" / "models" / "get_invoice_request.py").exists()
    assert not (generated_dir_path / "billing" / "models" / "get_invoice_response.py").exists()
    assert not (generated_dir_path / "billing" / "models" / "get_invoice_error.py").exists()

    post_apply_diff_plan = diff_service.run(tmp_path)
    post_apply_changes = [
        c for c in post_apply_diff_plan.changes if c.change_type in {"ADD", "UPDATE", "REMOVE"}
    ]
    assert post_apply_changes == []

    post_apply_check = service.run(tmp_path, check=True)
    assert post_apply_check.drift_status == "no-drift"
    assert not post_apply_check.drift_detected

    second_apply = service.run(tmp_path, baseline_ref="v1.0.0")
    assert second_apply.drift_status == "no-drift"
    assert second_apply.applied_changes == 0


def test_generate_check_detects_drift_for_changed_nested_field_description(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
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
    properties:
      invoice_id:
        type: string
        description: Invoice identifier
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    no_drift = service.run(tmp_path, check=True)
    assert not no_drift.drift_detected
    assert no_drift.drift_status == "no-drift"

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
    properties:
      invoice_id:
        type: string
        description: Changed nested field description
errors: []
""".strip(),
        encoding="utf-8",
    )

    drift = service.run(tmp_path, check=True)
    assert drift.drift_detected
    assert drift.drift_status == "drift"


def test_generate_filtered_scope_does_not_remove_artifacts_outside_selected_endpoints(
    tmp_path: Path,
) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "contracts" / "users").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )
    users_contract = tmp_path / ".apidev" / "contracts" / "users" / "get_user.yaml"
    users_contract.write_text(
        """
method: GET
path: /v1/users/{user_id}
auth: bearer
summary: Get user
description: Get user details
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      user_id:
        type: string
response:
  status: 200
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    users_route = tmp_path / ".apidev" / "output" / "api" / "users" / "routes" / "get_user.py"
    assert users_route.exists()

    users_contract.unlink()

    result = service.run(
        tmp_path,
        baseline_ref="v1.0.0",
        endpoint_filters=EndpointFilters(include=("billing_*",), exclude=()),
    )

    assert result.drift_status == "no-drift"
    assert users_route.exists()


def test_generate_emits_schema_example_and_openapi_example_metadata(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    response_model = generated_dir_path / "billing" / "models" / "get_invoice_response.py"
    operation_map = generated_dir_path / "operation_map.py"
    openapi_docs = generated_dir_path / "openapi_docs.py"

    response_source = response_model.read_text(encoding="utf-8")
    assert 'SCHEMA_EXAMPLE = {"invoice_id": "inv-001"}' in response_source

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map.read_text(encoding="utf-8"), {}, operation_map_namespace)
    operation_map_value = operation_map_namespace["OPERATION_MAP"]

    openapi_source = openapi_docs.read_text(encoding="utf-8")
    openapi_source = openapi_source.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = build_openapi_paths()

    get_operation = paths["/v1/invoices/{invoice_id}"]["get"]
    assert get_operation["responses"]["200"]["content"]["application/json"]["example"] == {
        "invoice_id": "inv-001"
    }
    assert get_operation["x-apidev-errors"][0]["example"] == {"code": "INVOICE_NOT_FOUND"}


def test_generate_openapi_extensions_enabled_by_default(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_source = (generated_dir_path / "operation_map.py").read_text(encoding="utf-8")
    openapi_docs_source = (generated_dir_path / "openapi_docs.py").read_text(encoding="utf-8")
    assert '"x-apidev-auth"' in openapi_docs_source
    assert '"x-apidev-deprecation"' in openapi_docs_source
    assert '"x-apidev-errors"' in openapi_docs_source

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_source, {}, operation_map_namespace)
    operation_map_value = operation_map_namespace["OPERATION_MAP"]

    openapi_source = openapi_docs_source.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = build_openapi_paths()

    get_operation = paths["/v1/invoices/{invoice_id}"]["get"]
    assert get_operation["x-apidev-auth"] == "bearer"
    assert get_operation["x-apidev-deprecation"] == {
        "status": "active",
        "deprecated_since_release": None,
    }
    assert get_operation["x-apidev-errors"] == []


def test_generate_openapi_extensions_can_be_disabled_without_affecting_core_fields(
    tmp_path: Path,
) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
        """
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[openapi]
include_extensions = false

[paths]
templates_dir = ".apidev/templates"
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_source = (generated_dir_path / "operation_map.py").read_text(encoding="utf-8")
    openapi_docs_source = (generated_dir_path / "openapi_docs.py").read_text(encoding="utf-8")
    assert "x-apidev-" not in openapi_docs_source

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_source, {}, operation_map_namespace)
    operation_map_value = operation_map_namespace["OPERATION_MAP"]

    openapi_source = openapi_docs_source.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = build_openapi_paths()

    get_operation = paths["/v1/invoices/{invoice_id}"]["get"]
    assert "x-apidev-auth" not in get_operation
    assert "x-apidev-deprecation" not in get_operation
    assert "x-apidev-errors" not in get_operation
    assert get_operation["operationId"] == "billing_get_invoice"
    assert get_operation["description"] == "Get invoice details"
    assert get_operation["tags"] == ["billing"]
    assert get_operation["security"] == [{"bearerAuth": []}]
    assert sorted(get_operation["responses"]) == ["200", "404"]


def test_generate_openapi_uses_contract_response_status(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "create_invoice.yaml").write_text(
        """
method: POST
path: /v1/invoices
auth: bearer
summary: Create invoice
description: Create invoice details
intent: write
access_pattern: imperative
response:
  status: 201
  body:
    type: object
    example:
      invoice_id: inv-001
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_source = (generated_dir_path / "operation_map.py").read_text(encoding="utf-8")
    openapi_docs_source = (generated_dir_path / "openapi_docs.py").read_text(encoding="utf-8")

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_source, {}, operation_map_namespace)
    operation_map_value = operation_map_namespace["OPERATION_MAP"]

    openapi_source = openapi_docs_source.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = build_openapi_paths()

    post_operation = paths["/v1/invoices"]["post"]
    assert "201" in post_operation["responses"]
    assert "200" not in post_operation["responses"]
    assert post_operation["responses"]["201"]["content"]["application/json"]["example"] == {
        "invoice_id": "inv-001"
    }


def test_generate_emits_deprecation_status_in_metadata_and_templates(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "release-state.json").write_text(
        json.dumps(
            {
                "release_number": 3,
                "baseline_ref": "v1.2.0",
                "deprecated_operations": {"billing_get_invoice": 2},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path)

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_source = (generated_dir_path / "operation_map.py").read_text(encoding="utf-8")
    router_source = (generated_dir_path / "billing" / "routes" / "get_invoice.py").read_text(
        encoding="utf-8"
    )
    response_source = (
        generated_dir_path / "billing" / "models" / "get_invoice_response.py"
    ).read_text(encoding="utf-8")
    openapi_docs = (generated_dir_path / "openapi_docs.py").read_text(encoding="utf-8")

    assert '"deprecation_status": "deprecated"' in operation_map_source
    assert '"deprecated_since_release": 2' in operation_map_source
    assert '"deprecation_status": "deprecated"' in router_source
    assert '"deprecated_since_release": 2' in router_source
    assert 'deprecation_status: str = "deprecated"' in response_source
    assert "deprecated_since_release: int | None = 2" in response_source

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_source, {}, operation_map_namespace)
    operation_map_value = operation_map_namespace["OPERATION_MAP"]

    openapi_source = openapi_docs.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = build_openapi_paths()
    get_operation = paths["/v1/invoices/{invoice_id}"]["get"]

    assert get_operation["deprecated"] is True
    assert get_operation["x-apidev-deprecation"] == {
        "status": "deprecated",
        "deprecated_since_release": 2,
    }


def test_generate_openapi_rejects_manual_tags_in_operation_metadata(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )

    _ = service.run(tmp_path, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_source = (generated_dir_path / "operation_map.py").read_text(encoding="utf-8")
    openapi_docs_source = (generated_dir_path / "openapi_docs.py").read_text(encoding="utf-8")

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_source, {}, operation_map_namespace)
    operation_map_value = cast(
        dict[str, dict[str, object]], operation_map_namespace["OPERATION_MAP"]
    )
    operation_map_value["billing_get_invoice"]["tags"] = ["manual"]

    openapi_source = openapi_docs_source.replace("from .operation_map import OPERATION_MAP\n\n", "")
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map_value}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])

    with pytest.raises(ValueError, match="MANUAL_TAGS_FORBIDDEN"):
        build_openapi_paths()
