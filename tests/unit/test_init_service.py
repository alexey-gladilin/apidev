from pathlib import Path

import pytest

from apidev.application.services.init_service import (
    InitPathBoundaryError,
    InitService,
)
from apidev.infrastructure.config.toml_loader import default_config_text
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


def _managed_template_paths(root: Path) -> list[Path]:
    templates_dir = root / ".apidev" / "templates"
    return [
        templates_dir / "generated_operation_map.py.j2",
        templates_dir / "generated_openapi_docs.py.j2",
        templates_dir / "generated_router.py.j2",
        templates_dir / "generated_schema.py.j2",
    ]


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


def test_init_creates_ref_based_sample_contract_and_shared_models(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )

    service.run(tmp_path)

    search_contract = (tmp_path / ".apidev" / "contracts" / "users" / "search.yaml").read_text(
        encoding="utf-8"
    )
    pagination_model = (
        tmp_path / ".apidev" / "models" / "common" / "pagination_request.yaml"
    ).read_text(encoding="utf-8")
    response_model = (
        tmp_path / ".apidev" / "models" / "users" / "search_users_response.yaml"
    ).read_text(encoding="utf-8")

    assert "path: /v1/users/search" in search_contract
    assert "$ref: common.PaginationRequest" in search_contract
    assert "$ref: users.SearchUsersResponse" in search_contract
    assert "contract_type: shared_model" in pagination_model
    assert "name: PaginationRequest" in pagination_model
    assert "items:\n        $ref: users.UserSummary" in response_model


def test_init_creates_managed_templates(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )

    service.run(tmp_path, integration_mode="full")

    for template_path in _managed_template_paths(tmp_path):
        assert template_path.exists()
        assert template_path.read_text(encoding="utf-8").strip()


def test_init_create_does_not_require_repair_for_modified_bootstrap_contract(
    tmp_path: Path,
) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "contracts" / "system" / "health.yaml").write_text(
        "method: POST\npath: /broken\nintent: write\naccess_pattern: imperative\n",
        encoding="utf-8",
    )

    result = service.run(tmp_path, mode="create")

    assert result.status == "already_initialized"
    assert "method: POST" in (
        tmp_path / ".apidev" / "contracts" / "system" / "health.yaml"
    ).read_text(encoding="utf-8")


def test_init_create_does_not_require_repair_for_modified_bootstrap_shared_model(
    tmp_path: Path,
) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "models" / "common" / "pagination_request.yaml").write_text(
        "contract_type: shared_model\nname: Broken\n",
        encoding="utf-8",
    )

    result = service.run(tmp_path, mode="create")

    assert result.status == "already_initialized"
    assert "name: Broken" in (
        tmp_path / ".apidev" / "models" / "common" / "pagination_request.yaml"
    ).read_text(encoding="utf-8")


def test_init_repair_overwrites_invalid_config_toml(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    config_path = tmp_path / ".apidev" / "config.toml"
    config_path.write_text("[generator]\nscaffold = \n", encoding="utf-8")

    result = service.run(tmp_path, mode="repair")

    assert result.status == "repaired"
    rewritten = config_path.read_text(encoding="utf-8")
    assert "[paths]" in rewritten
    assert "[inputs]" in rewritten
    assert "[generator]" in rewritten
    assert "version" not in rewritten


def test_init_force_overwrites_managed_config(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    config_path = tmp_path / ".apidev" / "config.toml"
    config_path.write_text("[generator]\nscaffold = \n", encoding="utf-8")

    result = service.run(tmp_path, mode="force")

    assert result.status == "forced"
    assert "[paths]" in config_path.read_text(encoding="utf-8")


def test_init_create_accepts_valid_custom_config(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "config.toml").write_text(
        """
[paths]
templates_dir = ".apidev/templates"
[inputs]
contracts_dir = "spec/contracts"
shared_models_dir = "spec/models"
[generator]
generated_dir = ".apidev/output/api"
""".strip() + "\n",
        encoding="utf-8",
    )

    result = service.run(tmp_path, mode="create")

    assert result.status == "initialized"
    assert (tmp_path / "spec" / "contracts").exists()


def test_init_repair_does_not_restore_missing_bootstrap_contract_in_custom_contracts_dir(
    tmp_path: Path,
) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "config.toml").write_text(
        """[inputs]
contracts_dir = "spec/contracts"
[generator]
generated_dir = ".apidev/output/api"
[paths]
templates_dir = ".apidev/templates"
""".strip() + "\n",
        encoding="utf-8",
    )

    custom_contract = tmp_path / "spec" / "contracts" / "system" / "health.yaml"
    custom_contract.parent.mkdir(parents=True, exist_ok=True)
    custom_contract.write_text(
        "method: GET\npath: /v1/health\nauth: public\nintent: read\naccess_pattern: cached\n",
        encoding="utf-8",
    )
    custom_contract.unlink()

    result = service.run(tmp_path, mode="repair")

    assert result.status == "repaired"
    assert not custom_contract.exists()


def test_init_repair_does_not_restore_missing_bootstrap_shared_model_in_custom_dir(
    tmp_path: Path,
) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "config.toml").write_text(
        """[inputs]
contracts_dir = "spec/contracts"
shared_models_dir = "spec/models"
[generator]
generated_dir = ".apidev/output/api"
[paths]
templates_dir = ".apidev/templates"
""".strip() + "\n",
        encoding="utf-8",
    )

    custom_model = tmp_path / "spec" / "models" / "common" / "pagination_request.yaml"
    custom_model.parent.mkdir(parents=True, exist_ok=True)
    custom_model.write_text(
        "contract_type: shared_model\nname: PaginationRequest\n", encoding="utf-8"
    )
    custom_model.unlink()

    result = service.run(tmp_path, mode="repair")

    assert result.status == "repaired"
    assert not custom_model.exists()


def test_init_repair_restores_missing_managed_template(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path, integration_mode="full")
    template_to_remove = tmp_path / ".apidev" / "templates" / "generated_router.py.j2"
    template_to_remove.unlink()

    result = service.run(tmp_path, mode="repair", integration_mode="full")

    assert result.status == "repaired"
    assert template_to_remove.exists()
    assert template_to_remove.read_text(encoding="utf-8").strip()


def test_init_repair_does_not_recreate_removed_sample_contract(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    contract_to_remove = tmp_path / ".apidev" / "contracts" / "users" / "search.yaml"
    contract_to_remove.unlink()

    result = service.run(tmp_path, mode="repair")

    assert result.status == "repaired"
    assert not contract_to_remove.exists()


def test_init_repair_does_not_recreate_removed_shared_model(tmp_path: Path) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    model_to_remove = tmp_path / ".apidev" / "models" / "users" / "user_summary.yaml"
    model_to_remove.unlink()

    result = service.run(tmp_path, mode="repair")

    assert result.status == "repaired"
    assert not model_to_remove.exists()


@pytest.mark.parametrize(
    ("contracts_dir", "templates_dir"),
    [
        ("/tmp/apidev-contracts-outside", ".apidev/templates"),
        (".apidev/contracts", "/tmp/apidev-templates-outside"),
        ("../contracts-outside", ".apidev/templates"),
        (".apidev/contracts", "../templates-outside"),
    ],
)
def test_init_repair_rejects_out_of_project_managed_dirs(
    tmp_path: Path,
    contracts_dir: str,
    templates_dir: str,
) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "config.toml").write_text(
        f"""[inputs]
contracts_dir = "{contracts_dir}"
[generator]
generated_dir = ".apidev/output/api"
[paths]
templates_dir = "{templates_dir}"
""".strip() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(InitPathBoundaryError):
        service.run(tmp_path, mode="repair")


@pytest.mark.parametrize(
    ("contracts_dir", "templates_dir"),
    [
        ("/tmp/apidev-contracts-outside-force", ".apidev/templates"),
        (".apidev/contracts", "/tmp/apidev-templates-outside-force"),
        ("../contracts-outside-force", ".apidev/templates"),
        (".apidev/contracts", "../templates-outside-force"),
    ],
)
def test_init_force_rejects_out_of_project_managed_dirs(
    tmp_path: Path,
    contracts_dir: str,
    templates_dir: str,
) -> None:
    service = InitService(
        fs=LocalFileSystem(),
        default_config_text=default_config_text(),
    )
    service.run(tmp_path)
    (tmp_path / ".apidev" / "config.toml").write_text(
        f"""[inputs]
contracts_dir = "{contracts_dir}"
[generator]
generated_dir = ".apidev/output/api"
[paths]
templates_dir = "{templates_dir}"
""".strip() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(InitPathBoundaryError):
        service.run(tmp_path, mode="force")
