"""AR-007: contracts/templates/generated paths are driven by config.toml."""

from __future__ import annotations

from pathlib import Path

from apidev.commands.generate_cmd import generate_command


def test_generate_uses_contracts_templates_and_generated_paths_from_config(
    tmp_path: Path,
) -> None:
    (tmp_path / "spec" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / "spec" / "templates").mkdir(parents=True)
    (tmp_path / ".apidev").mkdir()
    (tmp_path / ".apidev" / "config.toml").write_text(
        """
version = "1"

[contracts]
dir = "spec/contracts"

[generator]
generated_dir = "build/generated"

[templates]
dir = "spec/templates"
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "spec" / "contracts" / "billing" / "get_invoice.yaml").write_text(
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
    (tmp_path / "spec" / "templates" / "generated_router.py.j2").write_text(
        "# custom-template\noperation_id = '{{ operation.operation_id }}'\n",
        encoding="utf-8",
    )

    generate_command(project_dir=tmp_path, check=False, baseline_ref="v1.0.0")

    generated_router = tmp_path / "build" / "generated" / "billing" / "routes" / "get_invoice.py"
    assert generated_router.exists()
    assert "# custom-template" in generated_router.read_text(encoding="utf-8")
    assert not (tmp_path / "src" / "app" / "api" / "generated").exists()
