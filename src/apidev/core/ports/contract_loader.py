from pathlib import Path
from typing import Protocol

from apidev.core.models.operation import Operation


class ContractLoaderPort(Protocol):
    def load(self, contracts_root: Path) -> list[Operation]: ...
