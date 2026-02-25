from pathlib import Path
import tomllib

import tomli_w

from apidev.core.models.config import ApidevConfig
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.filesystem import FileSystemPort


def default_config_text() -> str:
    return tomli_w.dumps(ApidevConfig().model_dump())


class TomlConfigLoader(ConfigLoaderPort):
    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    def load(self, project_dir: Path) -> ApidevConfig:
        path = project_dir / ".apidev" / "config.toml"
        if not self.fs.exists(path):
            return ApidevConfig()

        data = tomllib.loads(self.fs.read_text(path))
        return ApidevConfig.model_validate(data)
