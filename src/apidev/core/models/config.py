from typing import Literal

from pydantic import BaseModel, field_validator


class ContractsConfig(BaseModel):
    dir: str = ".apidev/contracts"


class GeneratorConfig(BaseModel):
    generated_dir: str = ".apidev/output/api"
    postprocess: Literal["auto", "none", "ruff", "black"] = "auto"


class TemplatesConfig(BaseModel):
    dir: str = ".apidev/templates"


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
    evolution: EvolutionConfig = EvolutionConfig()
