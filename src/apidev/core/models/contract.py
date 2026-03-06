from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    local_models: dict[str, dict[str, Any]] = field(default_factory=dict)


class RefSchemaNodeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ref: str = Field(alias="$ref")
    required: bool | None = None
    description: str | None = None


class SharedModelContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_type: str = "shared_model"
    name: str
    description: str
    model: dict[str, Any]
