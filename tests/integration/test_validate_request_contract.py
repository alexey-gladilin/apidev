import json
from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _write_contract(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def test_validate_accepts_request_path_query_and_body(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/create_invoice.yaml",
        """
method: POST
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Create invoice
description: Create invoice
intent: write
access_pattern: imperative
request:
  path:
    type: object
    properties:
      invoice_id:
        type: string
        required: true
  query:
    type: object
    properties:
      expand:
        type: boolean
  body:
    type: object
    properties:
      currency:
        type: string
        required: true
response:
  status: 201
  body: {type: object}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["status"] == "ok"
    assert payload["diagnostics"] == []


def test_validate_request_unknown_fields_fail_fast_with_validation_code(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/create_invoice.yaml",
        """
method: POST
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Create invoice
description: Create invoice
intent: write
access_pattern: imperative
request:
  headers:
    type: object
    properties: {}
  query: invalid
response:
  status: 201
  body: {type: object}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    codes = [item["code"] for item in payload["diagnostics"]]
    locations = [item["location"] for item in payload["diagnostics"]]
    assert codes == ["validation.request-unknown-field"]
    assert locations == ["billing/create_invoice.yaml:request.headers"]


def test_validate_accepts_legacy_contract_without_request_when_no_path_placeholders(
    tmp_path: Path,
) -> None:
    _write_contract(
        tmp_path,
        "zeta/get_status.yaml",
        """
method: GET
path: /v1/status
auth: public
summary: Get status
description: Get status
intent: read
access_pattern: cached
response:
  status: 200
  body: {type: object}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["status"] == "ok"
    assert payload["diagnostics"] == []
