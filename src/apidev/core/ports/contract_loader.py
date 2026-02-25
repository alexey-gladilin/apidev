from pathlib import Path
from typing import Protocol

from apidev.core.models.operation import Operation


class ContractLoaderPort(Protocol):
    def load(self, project_dir: Path) -> list[Operation]: ...
