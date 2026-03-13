import json
from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app

runner = CliRunner()


def _write_contract(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _write_shared_model(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "models" / relpath
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
intent: write
access_pattern: imperative
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
    assert payload["diagnostics"][0]["code"].startswith("validation.")


def test_validate_json_output_reports_missing_required_metadata_deterministically(
    tmp_path: Path,
) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_contract.yaml",
        """
method: GET
path: /v1/invoices
auth: bearer
summary: Bad contract
description: Missing required metadata.
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
    assert payload["summary"]["errors"] >= 2
    missing_metadata = [
        item
        for item in payload["diagnostics"]
        if item["location"]
        in {
            "billing/bad_contract.yaml:access_pattern",
            "billing/bad_contract.yaml:intent",
        }
    ]
    assert [item["code"] for item in missing_metadata] == [
        "validation.schema-missing-field",
        "validation.schema-missing-field",
    ]
    assert [item["location"] for item in missing_metadata] == [
        "billing/bad_contract.yaml:access_pattern",
        "billing/bad_contract.yaml:intent",
    ]
    assert [item["rule"] for item in missing_metadata] == [
        "schema.contract.required_field",
        "schema.contract.required_field",
    ]
    assert all(item["category"] == "validation" for item in missing_metadata)


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


def test_validate_json_output_includes_machine_readable_cycle_diagnostics(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "common/a.yaml",
        """
contract_type: shared_model
name: A
description: A model
model:
  type: object
  properties:
    b:
      $ref: common.B
""",
    )
    _write_shared_model(
        tmp_path,
        "common/b.yaml",
        """
contract_type: shared_model
name: B
description: B model
model:
  type: object
  properties:
    a:
      $ref: common.A
""",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    cycle_diagnostics = [
        item
        for item in payload["diagnostics"]
        if item["code"] == "validation.contract-reference-cycle"
    ]
    assert cycle_diagnostics
    assert cycle_diagnostics[0]["context"]["cycle_path"] == [
        "shared_model:common.A",
        "shared_model:common.B",
        "shared_model:common.A",
    ]
