import json
from pathlib import Path

from typer.testing import CliRunner

from apidev.cli import app
from apidev.core.constants import APIDEV_DIRNAME, DEFAULT_RELEASE_STATE_FILE
from apidev.testing.config_helpers import write_config

runner = CliRunner()

CUSTOM_CONTRACTS_DIR = f"{APIDEV_DIRNAME}/custom/contracts"
CUSTOM_SHARED_MODELS_DIR = f"{APIDEV_DIRNAME}/custom/models"
CUSTOM_GENERATED_DIR = f"{APIDEV_DIRNAME}/custom/output/api"
CUSTOM_TEMPLATES_DIR = f"{APIDEV_DIRNAME}/custom/templates"
CUSTOM_RELEASE_STATE_FILE = f"{APIDEV_DIRNAME}/state/release-state.json"
BILLING_CONTRACT_RELPATH = "billing/get_invoice.yaml"
STRICT_COMPATIBILITY_POLICY = "strict"
RELEASE_STATE_INVALID_MARKER = "release-state-invalid"


def _write_custom_config(project_dir: Path) -> None:
    write_config(
        project_dir,
        f"""
[paths]
templates_dir = "{CUSTOM_TEMPLATES_DIR}"

[inputs]
contracts_dir = "{CUSTOM_CONTRACTS_DIR}"
shared_models_dir = "{CUSTOM_SHARED_MODELS_DIR}"

[generator]
generated_dir = "{CUSTOM_GENERATED_DIR}"

[evolution]
release_state_file = "{CUSTOM_RELEASE_STATE_FILE}"
compatibility_policy = "warn"
grace_period_releases = 2

[openapi]
include_extensions = true
""",
    )


def _write_contract(project_dir: Path) -> None:
    contract_path = project_dir / CUSTOM_CONTRACTS_DIR / BILLING_CONTRACT_RELPATH
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
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
""".strip() + "\n",
        encoding="utf-8",
    )


def _write_release_state(project_dir: Path, relpath: str, payload: dict[str, object]) -> Path:
    target = project_dir / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return target


def test_validate_uses_resolved_config_snapshot_with_custom_contracts_dir(tmp_path: Path) -> None:
    _write_custom_config(tmp_path)
    _write_contract(tmp_path)

    result = runner.invoke(app, ["validate", "--project-dir", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["status"] == "ok"
    assert payload["diagnostics"] == []


def test_diff_reads_release_state_from_evolution_override_not_default_path(
    tmp_path: Path,
) -> None:
    _write_custom_config(tmp_path)
    _write_contract(tmp_path)
    _write_release_state(
        tmp_path,
        CUSTOM_RELEASE_STATE_FILE,
        {"release_number": 2, "baseline_ref": "bad ref"},
    )
    _write_release_state(
        tmp_path,
        DEFAULT_RELEASE_STATE_FILE,
        {"release_number": 2, "baseline_ref": "v1.0.0"},
    )

    result = runner.invoke(
        app,
        [
            "diff",
            "--project-dir",
            str(tmp_path),
            "--compatibility-policy",
            STRICT_COMPATIBILITY_POLICY,
        ],
    )

    assert result.exit_code == 1
    assert RELEASE_STATE_INVALID_MARKER in result.output


def test_gen_applies_release_state_to_evolution_override_not_default_path(tmp_path: Path) -> None:
    _write_custom_config(tmp_path)
    _write_contract(tmp_path)

    result = runner.invoke(
        app,
        [
            "gen",
            "--project-dir",
            str(tmp_path),
            "--baseline-ref",
            "v1.0.0",
        ],
    )

    assert result.exit_code == 0
    custom_release_state_path = tmp_path / CUSTOM_RELEASE_STATE_FILE
    default_release_state_path = tmp_path / DEFAULT_RELEASE_STATE_FILE
    assert custom_release_state_path.exists()
    assert not default_release_state_path.exists()


def test_init_uses_same_config_snapshot_and_preserves_release_state_override(
    tmp_path: Path,
) -> None:
    _write_custom_config(tmp_path)

    result = runner.invoke(app, ["init", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / CUSTOM_CONTRACTS_DIR / "system" / "health.yaml").exists()
    assert not (tmp_path / DEFAULT_RELEASE_STATE_FILE).exists()

    config_text = (tmp_path / APIDEV_DIRNAME / "config.toml").read_text(encoding="utf-8")
    assert f'release_state_file = "{CUSTOM_RELEASE_STATE_FILE}"' in config_text
