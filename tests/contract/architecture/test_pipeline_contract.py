"""AR-005: diff and generate --check must be side-effect safe."""

from __future__ import annotations

from pathlib import Path

from apidev.application.services.diff_service import DiffService
from apidev.application.services.generate_service import GenerateService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
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
    )

    result = service.run(tmp_path, check=True)

    assert result.drift_detected
    assert writer.calls == []
    assert not (tmp_path / "src" / "app" / "api" / "generated").exists()
