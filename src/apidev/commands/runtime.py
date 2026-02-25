from pathlib import Path

from apidev.application.dto.resolved_paths import ResolvedPaths, resolve_paths
from apidev.core.models.config import ApidevConfig
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


def load_runtime(project_dir: Path) -> tuple[ApidevConfig, ResolvedPaths]:
    fs = LocalFileSystem()
    config = TomlConfigLoader(fs=fs).load(project_dir)
    paths = resolve_paths(project_dir, config)
    return config, paths
