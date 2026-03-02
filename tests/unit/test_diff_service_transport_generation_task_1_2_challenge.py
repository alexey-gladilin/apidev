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
scaffold = false
scaffold_dir = "integration"

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


def test_task_1_2_happy_path_public_auth_registry_refs(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "catalog/list_items.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: List items
description: List catalog items
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
    entry = operation_map_value["catalog_list_items"]

    assert entry["auth"] == "public"
    assert entry["router_module"] == "catalog.routes.list_items"
    assert entry["models"]["request"] == "catalog.models.list_items_request.CatalogListItemsRequest"
    assert entry["models"]["response"] == "catalog.models.list_items_response.CatalogListItemsResponse"
    assert entry["models"]["error"] == "catalog.models.list_items_error.CatalogListItemsError"


def test_task_1_2_defaults_auth_when_missing(tmp_path: Path) -> None:
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


def test_task_1_2_empty_contracts_directory_still_generates_registry(tmp_path: Path) -> None:
    _write_project_config(tmp_path)

    plan = _create_diff_service().run(tmp_path)
    planned = [change.path.relative_to(plan.generated_root).as_posix() for change in plan.changes]
    assert planned == ["operation_map.py", "openapi_docs.py"]


def test_task_1_2_boundary_short_domain_and_operation_segments(tmp_path: Path) -> None:
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
    assert entry["models"]["request"] == "a.models.b_request.ABRequest"
    assert entry["models"]["response"] == "a.models.b_response.ABResponse"
    assert entry["models"]["error"] == "a.models.b_error.ABError"


def test_task_1_2_error_invalid_yaml_fails_fast(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
response:
  status: [invalid
""",
    )

    with pytest.raises(ValueError, match="Invalid YAML"):
        _create_diff_service().run(tmp_path)
