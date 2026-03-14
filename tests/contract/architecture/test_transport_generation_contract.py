"""AR-008: transport generation keeps stable bridge and registry contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from apidev.commands.generate_cmd import generate_command


def test_generated_router_exposes_explicit_bridge_signature(tmp_path: Path) -> None:
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
intent: read
access_pattern: cached
summary: Get invoice
description: Get invoice details
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

    generate_command(project_dir=tmp_path, check=False, baseline_ref="v1.0.0")

    router_path = tmp_path / ".apidev" / "output" / "api" / "billing" / "routes" / "get_invoice.py"
    domain_init_path = tmp_path / ".apidev" / "output" / "api" / "billing" / "__init__.py"
    routes_init_path = (
        tmp_path / ".apidev" / "output" / "api" / "billing" / "routes" / "__init__.py"
    )
    models_init_path = (
        tmp_path / ".apidev" / "output" / "api" / "billing" / "models" / "__init__.py"
    )
    operation_map_path = tmp_path / ".apidev" / "output" / "api" / "operation_map.py"
    openapi_docs_path = tmp_path / ".apidev" / "output" / "api" / "openapi_docs.py"

    router_source = router_path.read_text(encoding="utf-8")
    operation_map_source = operation_map_path.read_text(encoding="utf-8")
    openapi_docs_source = openapi_docs_path.read_text(encoding="utf-8")

    assert "class HandlerBridge(Protocol):" in router_source
    assert "async def __call__(" in router_source
    assert "request: BillingGetInvoiceRequest" in router_source
    assert "-> BillingGetInvoiceResponse" in router_source
    assert "async def route(" in router_source
    assert "payload: dict[str, object]" in router_source
    assert "handler: HandlerBridge" in router_source
    assert "from ..models.get_invoice_request import BillingGetInvoiceRequest" in router_source
    assert "from ..models.get_invoice_response import BillingGetInvoiceResponse" in router_source
    assert "from ..models.get_invoice_error import BillingGetInvoiceError" in router_source
    assert domain_init_path.exists()
    assert routes_init_path.exists()
    assert models_init_path.exists()

    assert '"method": "GET"' in operation_map_source
    assert '"path": "/v1/invoices/{invoice_id}"' in operation_map_source
    assert '"description": "Get invoice details"' in operation_map_source
    assert '"deprecation_status": "active"' in operation_map_source
    assert '"deprecated_since_release": None' in operation_map_source
    assert '"contract_fingerprint": "' in operation_map_source
    assert '"auth": "bearer"' in operation_map_source
    assert '"router_module": "billing.routes.get_invoice"' in operation_map_source
    assert '"callable": "billing.routes.get_invoice.route"' in operation_map_source
    assert (
        '"request": "billing.models.get_invoice_request.BillingGetInvoiceRequest"'
        in operation_map_source
    )
    assert (
        '"response": "billing.models.get_invoice_response.BillingGetInvoiceResponse"'
        in operation_map_source
    )
    assert (
        '"error": "billing.models.get_invoice_error.BillingGetInvoiceError"' in operation_map_source
    )
    assert '"description": "Get invoice details"' in router_source
    assert '"deprecation_status": "active"' in router_source
    assert '"deprecated_since_release": None' in router_source
    assert '"contract_fingerprint": "' in router_source
    assert "def build_openapi_paths()" in openapi_docs_source
    assert '"description": str(entry.get("description", ""))' in openapi_docs_source
    assert '"deprecated": ' in openapi_docs_source
    assert 'entry.get("deprecation_status", "active")' in openapi_docs_source
    assert '"x-apidev-deprecation": {' in openapi_docs_source


def test_generate_rejects_unsafe_contract_path_for_codegen(tmp_path: Path) -> None:
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "unsafe.yaml").write_text(
        """
method: GET
path: '/x"+__import__("os").system("echo_INJECTED")+"'
auth: public
intent: read
access_pattern: cached
summary: Unsafe
description: Unsafe
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit):
        generate_command(project_dir=tmp_path, check=False)


def test_generated_transport_contract_keeps_legacy_request_backwards_compatibility(
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
intent: read
access_pattern: cached
summary: Get status
description: Returns status
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    generate_command(project_dir=tmp_path, check=False, baseline_ref="v1.0.0")

    generated_dir_path = tmp_path / ".apidev" / "output" / "api"
    operation_map_path = generated_dir_path / "operation_map.py"
    openapi_docs_path = generated_dir_path / "openapi_docs.py"
    request_model_path = generated_dir_path / "zeta" / "models" / "get_status_request.py"

    operation_map_namespace: dict[str, object] = {}
    exec(operation_map_path.read_text(encoding="utf-8"), {}, operation_map_namespace)
    operation_map = cast(dict[str, dict[str, object]], operation_map_namespace["OPERATION_MAP"])
    legacy_entry = operation_map["zeta_get_status"]

    assert legacy_entry["request"] == {"path": {}, "query": {}, "body": {}}

    request_model_source = request_model_path.read_text(encoding="utf-8")
    assert "SCHEMA_FRAGMENT = {}" in request_model_source

    openapi_source = openapi_docs_path.read_text(encoding="utf-8").replace(
        "from .operation_map import OPERATION_MAP\n\n", ""
    )
    openapi_namespace: dict[str, object] = {"OPERATION_MAP": operation_map}
    exec(openapi_source, openapi_namespace)
    build_openapi_paths = cast(Any, openapi_namespace["build_openapi_paths"])
    paths = cast(dict[str, dict[str, dict[str, object]]], build_openapi_paths())
    operation = paths["/v1/status"]["get"]

    assert "parameters" not in operation
    assert "requestBody" not in operation


def test_generate_rejects_unsafe_contract_filename_for_operation_id(tmp_path: Path) -> None:
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "bad-name.yaml").write_text(
        """
method: GET
path: /v1/items
auth: public
intent: read
access_pattern: cached
summary: Unsafe operation id
description: Unsafe operation id
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit):
        generate_command(project_dir=tmp_path, check=False)


def test_generated_openapi_contract_exposes_components_for_shared_refs(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "models" / "common").mkdir(parents=True)
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
    (tmp_path / ".apidev" / "models" / "common" / "page_request.yaml").write_text(
        """
contract_type: shared_model
name: PageRequest
description: Shared page request
model:
  type: object
  properties:
    number:
      type: integer
      required: true
    size:
      type: integer
      required: true
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".apidev" / "contracts" / "billing" / "list_invoices.yaml").write_text(
        """
method: POST
path: /v1/invoices/list
auth: bearer
intent: read
access_pattern: cached
summary: List invoices
description: List invoices
request:
  body:
    type: object
    properties:
      page:
        $ref: common.PageRequest
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    generate_command(project_dir=tmp_path, check=False, baseline_ref="v1.0.0")

    openapi_docs_path = tmp_path / ".apidev" / "output" / "api" / "openapi_docs.py"
    openapi_docs_source = openapi_docs_path.read_text(encoding="utf-8")

    assert "OPENAPI_COMPONENTS =" in openapi_docs_source
    assert "def build_openapi_components()" in openapi_docs_source
    assert "#/components/schemas/" in openapi_docs_source
    assert "from .operation_map import OPERATION_MAP" in openapi_docs_source
    assert "from operation_map import OPERATION_MAP" in openapi_docs_source


def test_generated_integration_contract_exposes_standard_openapi_assembly_helper(
    tmp_path: Path,
) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "models" / "common").mkdir(parents=True)
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
    (tmp_path / ".apidev" / "models" / "common" / "page_request.yaml").write_text(
        """
contract_type: shared_model
name: PageRequest
description: Shared page request
model:
  type: object
  properties:
    number:
      type: integer
      required: true
    size:
      type: integer
      required: true
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".apidev" / "contracts" / "billing" / "list_invoices.yaml").write_text(
        """
method: POST
path: /v1/invoices/list
auth: bearer
intent: read
access_pattern: cached
summary: List invoices
description: List invoices
request:
  body:
    type: object
    properties:
      page:
        $ref: common.PageRequest
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    generate_command(project_dir=tmp_path, check=False, baseline_ref="v1.0.0")

    openapi_docs_path = tmp_path / ".apidev" / "output" / "api" / "openapi_docs.py"
    router_factory_path = tmp_path / ".apidev" / "output" / "integration" / "router_factory.py"
    openapi_docs_source = openapi_docs_path.read_text(encoding="utf-8")
    router_factory_source = router_factory_path.read_text(encoding="utf-8")

    assert 'if "OPERATION_MAP" not in globals():' in openapi_docs_source
    assert "def assemble_openapi_schema(" in openapi_docs_source
    assert 'merged_components["schemas"] = merged_schemas' in openapi_docs_source
    assert "except (ImportError, KeyError)" in openapi_docs_source
    assert "GENERATED_API_PACKAGE = " in router_factory_source
    assert 'return importlib.import_module(f"{GENERATED_API_PACKAGE}.{module_name}")' in (
        router_factory_source
    )
    assert "_openapi_docs_module = _import_generated_module(\"openapi_docs\")" in router_factory_source
    assert "build_openapi_components = cast(" in router_factory_source
    assert "build_openapi_paths = cast(" in router_factory_source
    assert "def assemble_openapi_schema(" in router_factory_source
    assert 'schema["paths"] = build_openapi_paths()' in router_factory_source
    assert 'merged_components["schemas"] = merged_schemas' in router_factory_source
    assert "def install_openapi(app: Any) -> None:" in router_factory_source
