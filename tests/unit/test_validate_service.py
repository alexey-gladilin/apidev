from pathlib import Path

from apidev.application.services.validate_service import ValidateService
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader


def test_validate_reports_no_errors_for_minimal_contract(tmp_path: Path) -> None:
    contract_dir = tmp_path / ".apidev" / "contracts" / "billing"
    contract_dir.mkdir(parents=True)
    (contract_dir / "create_invoice.yaml").write_text("""
method: POST
path: /v1/invoices
auth: bearer
summary: Create invoice
description: Create invoice
response:
  status: 201
  body: {type: object}
errors: []
""".strip())

    service = ValidateService(loader=YamlContractLoader())
    result = service.run(tmp_path)

    assert not result.errors
    assert len(result.operations) == 1
