from dataclasses import dataclass
from pathlib import Path

from apidev.core.models.contract import EndpointContract


@dataclass(slots=True)
class Operation:
    operation_id: str
    contract: EndpointContract
    contract_relpath: Path
