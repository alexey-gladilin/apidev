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


def normalize_operation_metadata_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip().lower()


def collect_operation_metadata_errors(
    intent: object,
    access_pattern: object,
    *,
    reject_non_string: bool = False,
) -> dict[str, str]:
    errors: dict[str, str] = {}
    if reject_non_string:
        errors.update(
            _collect_operation_metadata_type_errors(
                intent=intent,
                access_pattern=access_pattern,
            )
        )

    errors.update(
        collect_operation_metadata_empty_value_errors(
            intent=intent,
            access_pattern=access_pattern,
        )
    )
    return errors


def _collect_operation_metadata_type_errors(
    *, intent: object, access_pattern: object
) -> dict[str, str]:
    errors: dict[str, str] = {}
    for field_name, value in (
        (OPERATION_INTENT_FIELD, intent),
        (ACCESS_PATTERN_FIELD, access_pattern),
    ):
        if value is None or isinstance(value, str):
            continue
        errors[field_name] = f"Field '{field_name}' must be a string when provided."
    return errors


def collect_operation_metadata_empty_value_errors(
    *, intent: object, access_pattern: object
) -> dict[str, str]:
    return _collect_operation_metadata_field_errors(
        intent=intent,
        access_pattern=access_pattern,
        reject_unknown=False,
    )


def collect_operation_metadata_allowed_value_errors(
    *, intent: object, access_pattern: object
) -> dict[str, str]:
    return _collect_operation_metadata_field_errors(
        intent=intent,
        access_pattern=access_pattern,
        reject_unknown=True,
    )


def _collect_operation_metadata_field_errors(
    *,
    intent: object,
    access_pattern: object,
    reject_unknown: bool,
) -> dict[str, str]:
    errors: dict[str, str] = {}
    for field_name, value, allowed_values in _operation_metadata_field_specs(
        intent=intent,
        access_pattern=access_pattern,
    ):
        if not isinstance(value, str):
            continue
        message = _validate_operation_metadata_value(
            field_name=field_name,
            normalized_value=normalize_operation_metadata_value(value),
            allowed_values=allowed_values,
            reject_unknown=reject_unknown,
        )
        if message is not None:
            errors[field_name] = message
    return errors


def _operation_metadata_field_specs(
    *, intent: object, access_pattern: object
) -> tuple[tuple[str, object, frozenset[str]], ...]:
    return (
        (OPERATION_INTENT_FIELD, intent, OPERATION_INTENT_VALUES),
        (ACCESS_PATTERN_FIELD, access_pattern, ACCESS_PATTERN_VALUES),
    )


def collect_operation_metadata_compatibility_errors(
    *, intent: object, access_pattern: object
) -> dict[str, str]:
    normalized_intent = normalize_operation_metadata_value(intent)
    normalized_access_pattern = normalize_operation_metadata_value(access_pattern)
    if (
        normalized_intent not in OPERATION_INTENT_VALUES
        or normalized_access_pattern not in ACCESS_PATTERN_VALUES
    ):
        return {}
    if normalized_access_pattern in OPERATION_ACCESS_PATTERN_COMPATIBILITY[normalized_intent]:
        return {}

    allowed_values = ", ".join(sorted(OPERATION_ACCESS_PATTERN_COMPATIBILITY[normalized_intent]))
    return {
        ACCESS_PATTERN_FIELD: (
            "Field 'access_pattern' is incompatible with "
            f"intent '{normalized_intent}'. Allowed values: {allowed_values}."
        )
    }


def _validate_operation_metadata_value(
    *,
    field_name: str,
    normalized_value: str | None,
    allowed_values: frozenset[str],
    reject_unknown: bool,
) -> str | None:
    if normalized_value is None:
        return None
    if not normalized_value:
        return f"Field '{field_name}' must be non-empty when provided."
    if not reject_unknown or normalized_value in allowed_values:
        return None
    return f"Field '{field_name}' must be one of: {', '.join(sorted(allowed_values))}."


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
