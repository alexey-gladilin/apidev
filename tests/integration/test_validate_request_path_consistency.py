import json
from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _write_contract(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def test_validate_fails_when_path_has_placeholder_without_request_path(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice
intent: read
access_pattern: cached
response:
  status: 200
  body: {type: object}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert [item["code"] for item in payload["diagnostics"]] == ["validation.missing-request-path"]


def test_validate_fails_when_request_path_mismatches_route_placeholders(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}/{line_id}
auth: bearer
summary: Get invoice
description: Get invoice
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
        required: true
response:
  status: 200
  body: {type: object}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert [item["code"] for item in payload["diagnostics"]] == ["validation.request-path-mismatch"]
