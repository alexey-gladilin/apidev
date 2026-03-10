from pathlib import Path

from apidev.application.dto.generation_plan import EndpointFilters
from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_project(tmp_path: Path) -> None:
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".apidev" / "contracts" / "users" / "get_user.yaml").write_text(
        """
method: GET
path: /v1/users/{user_id}
auth: bearer
intent: read
access_pattern: cached
summary: Get user
description: Get user details
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


def _service(tmp_path: Path) -> DiffService:
    fs = LocalFileSystem()
    return DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )


def test_diff_service_applies_include_exclude_endpoint_filters(tmp_path: Path) -> None:
    _write_project(tmp_path)
    service = _service(tmp_path)

    plan = service.run(
        tmp_path,
        endpoint_filters=EndpointFilters(include=("billing_*", "users_*"), exclude=("users_*",)),
    )
    changed_paths = [change.path.as_posix() for change in plan.changes]

    assert plan.diagnostics == []
    assert any(path.endswith("/billing/routes/get_invoice.py") for path in changed_paths)
    assert not any(path.endswith("/users/routes/get_user.py") for path in changed_paths)


def test_diff_service_reports_invalid_endpoint_pattern_diagnostic(tmp_path: Path) -> None:
    _write_project(tmp_path)
    service = _service(tmp_path)

    plan = service.run(tmp_path, endpoint_filters=EndpointFilters(include=("[",), exclude=()))

    assert [diagnostic.code for diagnostic in plan.diagnostics] == [
        "generation.invalid-endpoint-pattern"
    ]
    assert plan.diagnostics[0].location == "include-endpoint[0]"
    assert plan.diagnostics[0].detail == "malformed glob pattern"


def test_diff_service_reports_empty_effective_endpoint_set(tmp_path: Path) -> None:
    _write_project(tmp_path)
    service = _service(tmp_path)

    plan = service.run(
        tmp_path,
        endpoint_filters=EndpointFilters(include=("does-not-match-*",), exclude=()),
    )

    assert [diagnostic.code for diagnostic in plan.diagnostics] == [
        "generation.empty-endpoint-selection"
    ]
    assert plan.diagnostics[0].location == "endpoint-filters"
