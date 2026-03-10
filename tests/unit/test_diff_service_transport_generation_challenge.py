from pathlib import Path

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
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"
scaffold = false
scaffold_dir = "integration"

[paths]
templates_dir = ".apidev/templates"
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


def test_transport_generation_empty_contract_set_keeps_core_outputs(tmp_path: Path) -> None:
    _write_project_config(tmp_path)

    plan = _create_diff_service().run(tmp_path)
    planned_paths = [
        change.path.relative_to(plan.generated_dir_path).as_posix() for change in plan.changes
    ]

    assert planned_paths == ["operation_map.py", "openapi_docs.py"]


def test_transport_generation_handles_null_summary_with_required_description(tmp_path: Path) -> None:
    _write_project_config(tmp_path)
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
intent: read
access_pattern: cached
summary: null
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
errors: []
""",
    )

    plan = _create_diff_service().run(tmp_path)
    planned_paths = [
        change.path.relative_to(plan.generated_dir_path).as_posix() for change in plan.changes
    ]

    assert "billing/routes/get_invoice.py" in planned_paths
    assert "billing/models/get_invoice_request.py" in planned_paths
    operation_map = next(
        change for change in plan.changes if change.path.name == "operation_map.py"
    )
    assert '"summary":' not in operation_map.content
    assert '"description": "Get invoice details"' in operation_map.content


def test_transport_generation_rejects_nested_relpath_for_single_level_layout(
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
intent: read
access_pattern: cached
summary: Get invoice
description: Get invoice
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


def test_transport_generation_reports_invalid_yaml(tmp_path: Path) -> None:
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
