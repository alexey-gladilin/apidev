from pathlib import Path

from apidev.application.dto.resolved_paths import resolve_paths
from apidev.core.models.config import ApidevConfig


def test_resolve_paths_includes_default_shared_models_dir(tmp_path: Path) -> None:
    paths = resolve_paths(tmp_path, ApidevConfig())

    assert paths.shared_models_dir == tmp_path / ".apidev" / "models"


def test_resolve_paths_uses_custom_shared_models_dir(tmp_path: Path) -> None:
    config = ApidevConfig.model_validate({"contracts": {"shared_models_dir": "spec/models"}})

    paths = resolve_paths(tmp_path, config)

    assert paths.shared_models_dir == tmp_path / "spec" / "models"
