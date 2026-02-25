from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EndpointContract:
    source_path: Path
    method: str
    path: str
    auth: str
    summary: str
    description: str
    response_status: int
    response_body: dict[str, Any]
    errors: list[dict[str, Any]]
