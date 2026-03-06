from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EndpointContract:
    source_path: Path
    method: str
    path: str
    auth: str
    description: str
    response_status: int
    response_body: dict[str, Any]
    errors: list[dict[str, Any]]
    request_path: dict[str, Any] = field(default_factory=dict)
    request_query: dict[str, Any] = field(default_factory=dict)
    request_body: dict[str, Any] = field(default_factory=dict)
