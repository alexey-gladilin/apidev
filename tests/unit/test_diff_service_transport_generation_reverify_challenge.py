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


def test_registry_defaults_public_auth_when_auth_field_missing(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    operation_map = next(change for change in plan.changes if change.path.name == "operation_map.py")

    namespace: dict[str, object] = {}
    exec(operation_map.content, {}, namespace)
    operation_map_value = cast(dict[str, Any], namespace["OPERATION_MAP"])
    entry = operation_map_value["billing_get_invoice"]

    assert entry["auth"] == "public"
    assert entry["router_module"] == "billing.routes.get_invoice"
    models = cast(dict[str, str], entry["models"])
    assert models["request"] == "billing.models.get_invoice_request.BillingGetInvoiceRequest"
    assert models["response"] == "billing.models.get_invoice_response.BillingGetInvoiceResponse"
    assert models["error"] == "billing.models.get_invoice_error.BillingGetInvoiceError"


def test_diff_service_handles_empty_contract_directory(tmp_path: Path) -> None:
    _write_project_config(tmp_path)

    plan = _create_diff_service().run(tmp_path)
    planned_paths = [change.path.relative_to(plan.generated_root).as_posix() for change in plan.changes]

    assert planned_paths == ["operation_map.py", "openapi_docs.py"]


def test_registry_path_segments_work_for_short_domain_and_operation_names(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "a/b.yaml",
        """
method: GET
path: /v1/x
auth: bearer
summary: X
description: X
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    operation_map = next(change for change in plan.changes if change.path.name == "operation_map.py")
    namespace: dict[str, object] = {}
    exec(operation_map.content, {}, namespace)
    operation_map_value = cast(dict[str, Any], namespace["OPERATION_MAP"])
    entry = operation_map_value["a_b"]

    assert entry["router_module"] == "a.routes.b"
    models = cast(dict[str, str], entry["models"])
    assert models["request"] == "a.models.b_request.ABRequest"
    assert models["response"] == "a.models.b_response.ABResponse"
    assert models["error"] == "a.models.b_error.ABError"


def test_diff_service_raises_on_duplicate_operation_ids(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get-invoice.yaml",
        """
method: GET
path: /v1/invoices/a
auth: bearer
summary: Get A
description: Get A
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
path: /v1/invoices/b
auth: bearer
summary: Get B
description: Get B
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    with pytest.raises(ValueError):
        _create_diff_service().run(tmp_path)
