from pathlib import Path

from apidev.application.services.generate_service import GenerateService
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.writer import SafeWriter
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def test_generate_idempotent(tmp_path: Path) -> None:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text("""
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = "src/app/api/generated"

[templates]
dir = ".apidev/templates"
""".strip())
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text("""
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body: {type: object}
errors: []
""".strip())

    fs = LocalFileSystem()
    service = GenerateService(
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(project_dir=tmp_path),
        fs=fs,
        writer=SafeWriter(fs=fs),
    )

    first = service.run(tmp_path)
    second = service.run(tmp_path)

    assert first.applied_changes >= 1
    assert second.applied_changes == 0
