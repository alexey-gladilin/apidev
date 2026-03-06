from dataclasses import dataclass
from pathlib import Path

from apidev.core.models.config import ApidevConfig


@dataclass(slots=True)
class ResolvedPaths:
    apidev_dir: Path
    config_path: Path
    contracts_dir: Path
    shared_models_dir: Path
    templates_dir: Path
    generated_dir_path: Path


def _resolve(project_dir: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return project_dir / candidate


def resolve_paths(project_dir: Path, config: ApidevConfig) -> ResolvedPaths:
    apidev_dir = project_dir / ".apidev"
    return ResolvedPaths(
        apidev_dir=apidev_dir,
        config_path=apidev_dir / "config.toml",
        contracts_dir=_resolve(project_dir, config.contracts.dir),
        shared_models_dir=_resolve(project_dir, config.contracts.shared_models_dir),
        templates_dir=_resolve(project_dir, config.templates.dir),
        generated_dir_path=_resolve(project_dir, config.generator.generated_dir),
    )
