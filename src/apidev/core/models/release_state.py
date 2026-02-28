import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
_GIT_TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")


def validate_baseline_ref(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("must be a non-empty git tag or commit")
    if _GIT_SHA_RE.fullmatch(normalized) or _GIT_TAG_RE.fullmatch(normalized):
        return normalized
    raise ValueError("must be a valid git tag or commit (sha 7-40 hex)")


class ReleaseState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release_number: int
    baseline_ref: str
    released_at: str | None = None
    git_commit: str | None = None
    tag: str | None = None
    deprecated_operations: dict[str, int] = Field(default_factory=dict)

    @field_validator("release_number")
    @classmethod
    def _validate_release_number(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be >= 1")
        return value

    @field_validator("baseline_ref")
    @classmethod
    def _validate_baseline_ref(cls, value: str) -> str:
        return validate_baseline_ref(value)

    @field_validator("deprecated_operations")
    @classmethod
    def _validate_deprecated_operations(cls, value: dict[str, int]) -> dict[str, int]:
        normalized: dict[str, int] = {}
        for operation_id, deprecated_since in value.items():
            key = str(operation_id).strip()
            if not key:
                raise ValueError("operation id must be non-empty")
            if int(deprecated_since) < 1:
                raise ValueError("deprecated_since_release_number must be >= 1")
            normalized[key] = int(deprecated_since)
        return normalized
