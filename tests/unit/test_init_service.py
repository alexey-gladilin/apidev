from pathlib import Path

import pytest

from apidev.application.services.init_service import InitRepairRequiredError, InitService
from apidev.infrastructure.config.toml_loader import default_config_text
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


def test_init_writes_default_contract_with_property_level_required(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )

    first = service.run(tmp_path)
    second = service.run(tmp_path)

    contract = (tmp_path / ".apidev" / "contracts" / "system" / "health.yaml").read_text(
        encoding="utf-8"
    )

    assert "required: [status]" not in contract
    assert "required: [error_code, message]" not in contract
    assert "status:\n        type: string\n        required: true" in contract
    assert "error_code:\n          type: string\n          required: true" in contract
    assert "message:\n          type: string\n          required: true" in contract
    assert first.status == "initialized"
    assert second.status == "already_initialized"


def test_init_create_requires_repair_for_invalid_managed_file(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "contracts" / "system" / "health.yaml").write_text(
        "method: POST\npath: /broken\n",
        encoding="utf-8",
    )

    with pytest.raises(InitRepairRequiredError):
        service.run(tmp_path, mode="create")


def test_init_repair_overwrites_only_invalid_managed_files(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    config_path = tmp_path / ".apidev" / "config.toml"
    config_path.write_text('version = "999"\n', encoding="utf-8")

    result = service.run(tmp_path, mode="repair")

    assert result.status == "repaired"
    assert "version = \"1\"" in config_path.read_text(encoding="utf-8")


def test_init_force_overwrites_managed_files(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    contract_path = tmp_path / ".apidev" / "contracts" / "system" / "health.yaml"
    contract_path.write_text("method: DELETE\npath: /override\n", encoding="utf-8")

    result = service.run(tmp_path, mode="force")

    assert result.status == "forced"
    assert "method: GET" in contract_path.read_text(encoding="utf-8")
