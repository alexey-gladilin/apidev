"""AR-008: transport generation keeps stable bridge and registry contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from apidev.commands.generate_cmd import generate_command


def test_generated_router_exposes_explicit_bridge_signature(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
    assert '"summary": "Get invoice"' in operation_map_source
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
    assert '"summary": "Get invoice"' in router_source
    assert '"description": "Get invoice details"' in router_source
    assert '"deprecation_status": "active"' in router_source
    assert '"deprecated_since_release": None' in router_source
    assert '"contract_fingerprint": "' in router_source
    assert "def build_openapi_paths()" in openapi_docs_source
    assert '"summary": str(entry.get("summary", ""))' in openapi_docs_source
    assert '"description": str(entry.get("description", ""))' in openapi_docs_source
    assert '"deprecated": ' in openapi_docs_source
    assert 'entry.get("deprecation_status", "active")' in openapi_docs_source
    assert '"x-apidev-deprecation": {' in openapi_docs_source


def test_generate_rejects_unsafe_contract_path_for_codegen(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "unsafe.yaml").write_text(
        """
method: GET
path: '/x"+__import__("os").system("echo_INJECTED")+"'
auth: public
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


def test_generate_rejects_unsafe_contract_filename_for_operation_id(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
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
    (tmp_path / ".apidev" / "contracts" / "billing" / "bad-name.yaml").write_text(
        """
method: GET
path: /v1/items
auth: public
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
