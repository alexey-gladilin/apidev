from pathlib import Path
from typing import Protocol

from apidev.core.models.config import ApidevConfig
from apidev.core.models.release_state import ReleaseState


class ConfigLoaderPort(Protocol):
    def load(self, project_dir: Path) -> ApidevConfig: ...
    def load_release_state(self, project_dir: Path, config: ApidevConfig) -> ReleaseState: ...
