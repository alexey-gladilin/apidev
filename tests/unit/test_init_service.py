from pathlib import Path

from apidev.application.services.init_service import InitService
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


def test_init_writes_default_contract_with_property_level_required(tmp_path: Path) -> None:
    service = InitService(fs=LocalFileSystem())

    service.run(tmp_path)

    contract = (tmp_path / ".apidev" / "contracts" / "system" / "health.yaml").read_text(
        encoding="utf-8"
    )

    assert "required: [status]" not in contract
    assert "required: [error_code, message]" not in contract
    assert "status:\n        type: string\n        required: true" in contract
    assert "error_code:\n          type: string\n          required: true" in contract
    assert "message:\n          type: string\n          required: true" in contract
