from pathlib import Path
from typing import cast

from pydantic import BaseModel, field_validator

from apidev.core.constants import (
    CompatibilityPolicyValue,
    DEFAULT_COMPATIBILITY_POLICY,
    DEFAULT_CONTRACTS_DIR,
    DEFAULT_GENERATED_DIR,
    DEFAULT_RELEASE_STATE_FILE,
    DEFAULT_SCAFFOLD_WRITE_POLICY,
    DEFAULT_SHARED_MODELS_DIR,
    DEFAULT_TEMPLATES_DIR,
    SCAFFOLD_WRITE_POLICIES,
    SCAFFOLD_WRITE_POLICIES_DISPLAY,
    DEFAULT_INTEGRATION_DIR,
    ScaffoldWritePolicy,
)
from apidev.core.ports.python_postprocessor import PythonPostprocessMode


class ContractsConfig(BaseModel):
    dir: str = DEFAULT_CONTRACTS_DIR
    shared_models_dir: str = DEFAULT_SHARED_MODELS_DIR


class GeneratorConfig(BaseModel):
    generated_dir: str = DEFAULT_GENERATED_DIR
    postprocess: PythonPostprocessMode = "auto"
    scaffold: bool = True
    scaffold_dir: str = DEFAULT_INTEGRATION_DIR
    scaffold_write_policy: ScaffoldWritePolicy = DEFAULT_SCAFFOLD_WRITE_POLICY

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
    def _validate_scaffold_write_policy(cls, value: str) -> ScaffoldWritePolicy:
        candidate = value.strip().lower()
        if candidate not in SCAFFOLD_WRITE_POLICIES:
            raise ValueError(f"must be one of: {SCAFFOLD_WRITE_POLICIES_DISPLAY}")
        return cast(ScaffoldWritePolicy, candidate)


class TemplatesConfig(BaseModel):
    dir: str = DEFAULT_TEMPLATES_DIR


class OpenAPIConfig(BaseModel):
    include_extensions: bool = True


class EvolutionConfig(BaseModel):
    compatibility_policy: CompatibilityPolicyValue = DEFAULT_COMPATIBILITY_POLICY
    grace_period_releases: int = 2
    release_state_file: str = DEFAULT_RELEASE_STATE_FILE

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
