from pathlib import Path

from apidev.application.services.generate_service import GenerateService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
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
generated_dir = ".apidev/output/api"

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
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
    )

    first = service.run(tmp_path)
    second = service.run(tmp_path)

    assert first.applied_changes >= 1
    assert second.applied_changes == 0


def test_generate_creates_runnable_transport_skeleton(tmp_path: Path) -> None:
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
  body:
    type: object
    properties:
      invoice_id:
        type: string
        description: Invoice identifier
errors:
  - code: INVOICE_NOT_FOUND
    http_status: 404
    body: {type: object}
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
    )

    result = service.run(tmp_path)

    assert result.applied_changes >= 5
    generated_root = tmp_path / ".apidev" / "output" / "api"
    router = generated_root / "routers" / "billing_get_invoice.py"
    openapi_docs = generated_root / "openapi_docs.py"
    request_model = generated_root / "transport" / "models" / "billing_get_invoice_request.py"
    response_model = generated_root / "transport" / "models" / "billing_get_invoice_response.py"
    error_model = generated_root / "transport" / "models" / "billing_get_invoice_error.py"

    assert router.exists()
    assert openapi_docs.exists()
    assert request_model.exists()
    assert response_model.exists()
    assert error_model.exists()

    compile(router.read_text(encoding="utf-8"), str(router), "exec")
    compile(openapi_docs.read_text(encoding="utf-8"), str(openapi_docs), "exec")
    compile(request_model.read_text(encoding="utf-8"), str(request_model), "exec")
    compile(response_model.read_text(encoding="utf-8"), str(response_model), "exec")
    compile(error_model.read_text(encoding="utf-8"), str(error_model), "exec")
    assert '"description": "Invoice identifier"' in response_model.read_text(encoding="utf-8")


def test_generate_check_detects_drift_for_changed_contract(tmp_path: Path) -> None:
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
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
    contract_path.write_text(
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

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
    )

    _ = service.run(tmp_path)

    no_drift = service.run(tmp_path, check=True)
    assert not no_drift.drift_detected

    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}/details
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

    drift = service.run(tmp_path, check=True)
    assert drift.drift_detected


def test_generate_check_detects_drift_for_changed_description(tmp_path: Path) -> None:
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
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
    contract_path.write_text(
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

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
    )

    _ = service.run(tmp_path)

    no_drift = service.run(tmp_path, check=True)
    assert not no_drift.drift_detected

    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Updated description for swagger
response:
  status: 200
  body: {type: object}
errors: []
""".strip(),
        encoding="utf-8",
    )

    drift = service.run(tmp_path, check=True)
    assert drift.drift_detected


def test_generate_check_detects_drift_for_changed_nested_field_description(tmp_path: Path) -> None:
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
    contract_path = tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml"
    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body:
    type: object
    properties:
      invoice_id:
        type: string
        description: Invoice identifier
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
    )

    _ = service.run(tmp_path)

    no_drift = service.run(tmp_path, check=True)
    assert not no_drift.drift_detected

    contract_path.write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body:
    type: object
    properties:
      invoice_id:
        type: string
        description: Changed nested field description
errors: []
""".strip(),
        encoding="utf-8",
    )

    drift = service.run(tmp_path, check=True)
    assert drift.drift_detected
