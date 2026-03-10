from pathlib import Path

from apidev.application.dto.generation_plan import GenerateResult, GenerationPlan
from apidev.application.services.diff_service import DiffService
from apidev.application.services.generate_service import GenerateService
from apidev.commands.diff_cmd import diff_command
from apidev.commands.generate_cmd import generate_command


def _write_project(project_dir: Path, scaffold: bool = False) -> None:
    (project_dir / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        f"""
[inputs]
contracts_dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"
scaffold = {str(scaffold).lower()}
scaffold_dir = "integration"

[paths]
templates_dir = ".apidev/templates"
""".strip() + "\n",
        encoding="utf-8",
    )
    (project_dir / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
intent: read
access_pattern: cached
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


def test_diff_command_passes_scaffold_true_override(monkeypatch, tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=False)
    captured: dict[str, object] = {}

    def _fake_run(
        self, project_dir: Path, compatibility_policy="warn", baseline_ref=None, scaffold=None
    ):
        captured["scaffold"] = scaffold
        return GenerationPlan(generated_dir_path=project_dir / ".apidev" / "output" / "api")

    monkeypatch.setattr(DiffService, "run", _fake_run)

    diff_command(
        project_dir=tmp_path,
        scaffold=True,
        no_scaffold=False,
        compatibility_policy=None,
        baseline_ref=None,
    )

    assert captured["scaffold"] is True


def test_generate_command_passes_scaffold_false_override(monkeypatch, tmp_path: Path) -> None:
    _write_project(tmp_path, scaffold=True)
    captured: dict[str, object] = {}

    def _fake_run(
        self,
        project_dir: Path,
        check: bool = False,
        compatibility_policy="warn",
        baseline_ref=None,
        scaffold=None,
        endpoint_filters=None,
    ):
        captured["scaffold"] = scaffold
        return GenerateResult(applied_changes=0)

    monkeypatch.setattr(GenerateService, "run", _fake_run)

    generate_command(
        project_dir=tmp_path,
        scaffold=False,
        no_scaffold=True,
        compatibility_policy=None,
        baseline_ref=None,
    )

    assert captured["scaffold"] is False
