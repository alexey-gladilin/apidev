"""AR-005: diff and generate --check must be side-effect safe."""

from __future__ import annotations

import json
import os
from pathlib import Path

from apidev.application.services.diff_service import DiffService
from apidev.application.services.generate_service import GenerateService
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
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )


class RecordingWriter:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path]] = []

    def write(self, generated_root: Path, target: Path, content: str) -> None:
        self.calls.append((generated_root, target))


def test_diff_does_not_write_files(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    fs = LocalFileSystem()
    service = DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )

    plan = service.run(tmp_path)

    assert plan.changes
    assert not (tmp_path / "src" / "app" / "api" / "generated").exists()


def test_generate_check_has_no_write_side_effects(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    fs = LocalFileSystem()
    writer = RecordingWriter()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=writer,
        postprocessor=PythonPostprocessor(),
    )

    result = service.run(tmp_path, check=True)

    assert result.drift_detected
    assert result.drift_status == "drift"
    assert writer.calls == []
    assert not (tmp_path / "src" / "app" / "api" / "generated").exists()


def test_diff_plan_is_byte_stable_for_reordered_optional_dbspec_hint_lists(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
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
errors: []
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".dbspec").mkdir(parents=True)

    hints_a = {
        "operations": {
            "billing_get_invoice": {
                "response_body": {
                    "properties": {"invoice_id": {"enum": ["PAID", "DRAFT", "VOID"]}}
                }
            }
        }
    }
    (tmp_path / ".dbspec" / "apidev-hints.json").write_text(
        json.dumps(hints_a, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )

    first_plan = service.run(tmp_path)
    first_response_model = next(
        change.content
        for change in first_plan.changes
        if change.path.as_posix().endswith("billing_get_invoice_response.py")
    )

    hints_b = {
        "operations": {
            "billing_get_invoice": {
                "response_body": {
                    "properties": {"invoice_id": {"enum": ["VOID", "PAID", "DRAFT"]}}
                }
            }
        }
    }
    (tmp_path / ".dbspec" / "apidev-hints.json").write_text(
        json.dumps(hints_b, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    second_plan = service.run(tmp_path)
    second_response_model = next(
        change.content
        for change in second_plan.changes
        if change.path.as_posix().endswith("billing_get_invoice_response.py")
    )

    assert first_response_model == second_response_model


def test_diff_ignores_optional_dbspec_hints_symlink_pointing_outside_project_root(
    tmp_path: Path,
) -> None:
    _write_minimal_project(tmp_path)
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
errors: []
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".dbspec").mkdir(parents=True)

    outside_hints_path = tmp_path.parent / "outside-apidev-hints.json"
    outside_hints_path.write_text(
        json.dumps(
            {
                "operations": {
                    "billing_get_invoice": {
                        "response_body": {
                            "properties": {
                                "db_only": {"type": "integer"},
                            }
                        }
                    }
                }
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    os.symlink(
        outside_hints_path,
        tmp_path / ".dbspec" / "apidev-hints.json",
    )

    fs = LocalFileSystem()
    service = DiffService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        postprocessor=PythonPostprocessor(),
    )

    plan = service.run(tmp_path)
    response_model = next(
        change.content
        for change in plan.changes
        if change.path.as_posix().endswith("billing_get_invoice_response.py")
    )
    assert '"invoice_id": {"type": "string"}' in response_model
    assert '"db_only"' not in response_model
