from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

OPERATION_INTENT_FIELD = "intent"
ACCESS_PATTERN_FIELD = "access_pattern"
OPERATION_METADATA_FIELDS = (OPERATION_INTENT_FIELD, ACCESS_PATTERN_FIELD)
OPERATION_INTENT_VALUES = frozenset({"read", "write"})
ACCESS_PATTERN_VALUES = frozenset({"cached", "imperative", "both", "none"})
OPERATION_ACCESS_PATTERN_COMPATIBILITY = {
    "read": ACCESS_PATTERN_VALUES,
    "write": frozenset({"imperative", "none"}),
}


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
    intent: str | None = None
    access_pattern: str | None = None
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
