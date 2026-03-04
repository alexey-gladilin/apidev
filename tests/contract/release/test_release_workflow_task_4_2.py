from __future__ import annotations

from pathlib import Path

import pytest

from apidev.application.services.init_service import InitService
from apidev.infrastructure.config.toml_loader import default_config_text
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem

_SCAFFOLD_FASTAPI = {
    "integration_handler_registry.py.j2",
    "integration_router_factory.py.j2",
    "integration_auth_registry.py.j2",
    "integration_error_mapper.py.j2",
}
_SCAFFOLD_RUNTIME_NONE = {
    "integration_handler_registry.py.j2",
    "integration_error_mapper.py.j2",
}
_FULL_FASTAPI = _SCAFFOLD_FASTAPI | {
    "generated_operation_map.py.j2",
    "generated_openapi_docs.py.j2",
    "generated_router.py.j2",
    "generated_schema.py.j2",
}


def _managed_templates(root: Path) -> set[str]:
    templates_dir = root / ".apidev" / "templates"
    return {path.name for path in templates_dir.glob("*.j2")} if templates_dir.exists() else set()


@pytest.mark.parametrize(
    ("runtime", "integration_mode", "expected_templates"),
    [
        ("fastapi", "off", set()),
        ("none", "off", set()),
        ("fastapi", "scaffold", _SCAFFOLD_FASTAPI),
        ("none", "scaffold", _SCAFFOLD_RUNTIME_NONE),
        ("fastapi", "full", _FULL_FASTAPI),
    ],
)
def test_init_profile_matrix_manages_expected_templates(
    tmp_path: Path,
    runtime: str,
    integration_mode: str,
    expected_templates: set[str],
) -> None:
    service = InitService(fs=LocalFileSystem(), default_config_text=default_config_text())

    result = service.run(tmp_path, runtime=runtime, integration_mode=integration_mode)

    assert result.status == "initialized"
    assert _managed_templates(tmp_path) == expected_templates


def test_init_profile_matrix_rejects_runtime_none_with_full_mode(tmp_path: Path) -> None:
    service = InitService(fs=LocalFileSystem(), default_config_text=default_config_text())

    with pytest.raises(ValueError, match="config.INIT_MODE_CONFLICT"):
        service.run(tmp_path, runtime="none", integration_mode="full")
