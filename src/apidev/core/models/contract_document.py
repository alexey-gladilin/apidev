from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class ContractDocument:
    source_path: Path
    contract_relpath: Path
    data: Any
    parse_error: str | None = None
