from pathlib import Path
from typing import Protocol

from apidev.core.models.config import ApidevConfig


class ConfigLoaderPort(Protocol):
    def load(self, project_dir: Path) -> ApidevConfig: ...
