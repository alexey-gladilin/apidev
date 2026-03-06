from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, field_validator


class ContractsConfig(BaseModel):
    dir: str = ".apidev/contracts"
    shared_models_dir: str = ".apidev/models"


class GeneratorConfig(BaseModel):
    generated_dir: str = ".apidev/output/api"
    postprocess: Literal["auto", "none", "ruff", "black"] = "auto"
    scaffold: bool = True
    scaffold_dir: str = "integration"
    scaffold_write_policy: Literal["create-missing", "skip-existing", "fail-on-conflict"] = (
        "create-missing"
    )

    @field_validator("generated_dir")
    @classmethod
    def _validate_generated_dir(cls, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise ValueError("must be a non-empty path")
        if Path(candidate).is_absolute():
            raise ValueError("absolute paths are not allowed")
        return value

    @field_validator("scaffold_dir")
    @classmethod
    def _validate_scaffold_dir(cls, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise ValueError("must be a non-empty path")
        if Path(candidate).is_absolute():
            raise ValueError("absolute paths are not allowed")
        return value

    @field_validator("scaffold_write_policy")
    @classmethod
    def _validate_scaffold_write_policy(
        cls, value: str
    ) -> Literal["create-missing", "skip-existing", "fail-on-conflict"]:
        candidate = value.strip().lower()
        allowed = ("create-missing", "skip-existing", "fail-on-conflict")
        if candidate not in allowed:
            raise ValueError("must be one of: create-missing, skip-existing, fail-on-conflict")
        return cast(Literal["create-missing", "skip-existing", "fail-on-conflict"], candidate)


class TemplatesConfig(BaseModel):
    dir: str = ".apidev/templates"


class OpenAPIConfig(BaseModel):
    include_extensions: bool = True


class EvolutionConfig(BaseModel):
    compatibility_policy: Literal["warn", "strict"] = "warn"
    grace_period_releases: int = 2
    release_state_file: str = ".apidev/release-state.json"

    @field_validator("grace_period_releases")
    @classmethod
    def _validate_grace_period_releases(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be >= 1")
        return value

    @field_validator("release_state_file")
    @classmethod
    def _validate_release_state_file(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-empty path")
        return value


class ApidevConfig(BaseModel):
    version: str = "1"
    contracts: ContractsConfig = ContractsConfig()
    generator: GeneratorConfig = GeneratorConfig()
    templates: TemplatesConfig = TemplatesConfig()
    openapi: OpenAPIConfig = OpenAPIConfig()
    evolution: EvolutionConfig = EvolutionConfig()
