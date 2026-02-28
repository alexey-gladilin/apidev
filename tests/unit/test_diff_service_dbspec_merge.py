"""Unit tests for DiffService optional dbspec hints merge and canonicalize behavior."""

import json
from pathlib import Path

from apidev.application.services.diff_service import DiffService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _write_minimal_project(tmp_path: Path) -> None:
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
    properties:
      invoice_id:
        type: string
errors:
  - code: INVOICE_NOT_FOUND
    http_status: 404
    body:
      type: object
      properties:
        code:
          type: string
""".strip(),
        encoding="utf-8",
    )


def _create_diff_service() -> DiffService:
    fs = LocalFileSystem()
    return DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )


def test_invalid_json_optional_hints_returns_empty_workflow_continues(tmp_path: Path) -> None:
    """Invalid JSON in apidev-hints.json must not block workflow; hints are ignored."""
    _write_minimal_project(tmp_path)
    (tmp_path / ".dbspec").mkdir(parents=True)
    (tmp_path / ".dbspec" / "apidev-hints.json").write_text(
        "{ invalid json }",
        encoding="utf-8",
    )

    plan = _create_diff_service().run(tmp_path)
    assert plan.changes
    response_model = next(
        change.content
        for change in plan.changes
        if change.path.as_posix().endswith("billing_get_invoice_response.py")
    )
    assert '"invoice_id": {"type": "string"}' in response_model


def test_empty_operations_hints_returns_operations_unchanged(tmp_path: Path) -> None:
    """Empty operations object in hints must not alter operations; output matches no-hints case."""
    _write_minimal_project(tmp_path)
    (tmp_path / ".dbspec").mkdir(parents=True)
    (tmp_path / ".dbspec" / "apidev-hints.json").write_text(
        '{"operations":{}}',
        encoding="utf-8",
    )

    plan_with_empty_hints = _create_diff_service().run(tmp_path)
    (tmp_path / ".dbspec" / "apidev-hints.json").unlink()

    plan_without_hints = _create_diff_service().run(tmp_path)

    response_with = next(
        c.content for c in plan_with_empty_hints.changes
        if c.path.as_posix().endswith("billing_get_invoice_response.py")
    )
    response_without = next(
        c.content for c in plan_without_hints.changes
        if c.path.as_posix().endswith("billing_get_invoice_response.py")
    )
    assert response_with == response_without


def test_merge_error_body_hints_with_valid_code_http_status_applies_hint(tmp_path: Path) -> None:
    """Error body hints with valid code and http_status must be merged into contract errors."""
    _write_minimal_project(tmp_path)
    (tmp_path / ".dbspec").mkdir(parents=True)
    (tmp_path / ".dbspec" / "apidev-hints.json").write_text(
        '{"operations":{"billing_get_invoice":{"errors":[{"code":"INVOICE_NOT_FOUND","http_status":404,'
        '"body":{"properties":{"hint_field":{"type":"integer"}}}}]}}}',
        encoding="utf-8",
    )

    plan = _create_diff_service().run(tmp_path)
    error_model = next(
        change.content
        for change in plan.changes
        if change.path.as_posix().endswith("billing_get_invoice_error.py")
    )
    assert '"hint_field"' in error_model
    assert '"type": "integer"' in error_model


def test_merge_canonicalize_recursion_depth_limit_does_not_stack_overflow(tmp_path: Path) -> None:
    """Deeply nested hints must not cause stack overflow; recursion is bounded."""
    _write_minimal_project(tmp_path)
    (tmp_path / ".apidev" / "config.toml").write_text(
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"
postprocess = "none"

[templates]
dir = ".apidev/templates"
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".dbspec").mkdir(parents=True)
    nested: dict = {"x": None}
    for _ in range(200):
        nested = {"inner": nested}

    (tmp_path / ".dbspec" / "apidev-hints.json").write_text(
        json.dumps({
            "operations": {
                "billing_get_invoice": {
                    "response_body": nested,
                }
            }
        }, separators=(",", ":")),
        encoding="utf-8",
    )

    plan = _create_diff_service().run(tmp_path)
    assert plan.changes

    # Truncation must produce safe output (no deep refs reaching _stable_python_literal).
    response_content = next(
        c.content for c in plan.changes
        if c.path.as_posix().endswith("billing_get_invoice_response.py")
    )
    assert '"<truncated>"' in response_content


def test_merge_deterministic_contract_priority(tmp_path: Path) -> None:
    """Contract fields must override hint fields; merge output must be deterministic."""
    _write_minimal_project(tmp_path)
    (tmp_path / ".dbspec").mkdir(parents=True)
    (tmp_path / ".dbspec" / "apidev-hints.json").write_text(
        '{"operations":{"billing_get_invoice":{"response_body":{"properties":{"invoice_id":'
        '{"type":"integer","nullable":true},"db_only":{"type":"integer"}}}}}}',
        encoding="utf-8",
    )

    plan = _create_diff_service().run(tmp_path)
    response_model = next(
        change.content
        for change in plan.changes
        if change.path.as_posix().endswith("billing_get_invoice_response.py")
    )
    assert '"type": "string"' in response_model
    assert '"db_only"' in response_model
