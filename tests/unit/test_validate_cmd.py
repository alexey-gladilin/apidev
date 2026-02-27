import json
from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _write_contract(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def test_validate_json_output_success(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/create_invoice.yaml",
        """
method: POST
path: /v1/invoices
auth: bearer
summary: Create invoice
description: Create invoice
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
    assert payload["summary"]["errors"] == 0
    assert payload["diagnostics"] == []


def test_validate_json_output_failure(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_contract.yaml",
        """
path: bad
auth: bearer
summary: Bad contract
description: Bad contract
response:
  status: 200
  body: {}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["summary"]["status"] == "failed"
    assert payload["summary"]["errors"] >= 1
    assert payload["diagnostics"][0]["code"].startswith("SCHEMA_")


def test_validate_human_output_remains_default(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_contract.yaml",
        """
path: bad
auth: bearer
summary: Bad contract
description: Bad contract
response:
  status: 200
  body: {}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert "SCHEMA_" in result.output
    assert '"diagnostics"' not in result.output


def test_validate_rejects_invalid_method_in_human_mode(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "system/health.yaml",
        """
method: GETоооо
path: /v1/health
auth: public
summary: Health endpoint
description: Returns health status.
response:
  status: 200
  body:
    type: object
    properties: {}
errors: []
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert "method" in result.output
    assert "SCHEMA_INVALID_VALUE" in result.output
