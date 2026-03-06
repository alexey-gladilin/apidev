from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, field_validator

from apidev.core.constants import (
    CompatibilityPolicyValue,
    VALIDATION_MSG_ABSOLUTE_PATHS_NOT_ALLOWED,
    VALIDATION_MSG_NON_EMPTY_PATH,
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

_EXTRA_FORBID = ConfigDict(extra="forbid")


class ContractsConfig(BaseModel):
    model_config = _EXTRA_FORBID

    dir: str = DEFAULT_CONTRACTS_DIR
    shared_models_dir: str = DEFAULT_SHARED_MODELS_DIR


class InputsConfig(BaseModel):
    model_config = _EXTRA_FORBID

    contracts_dir: str = DEFAULT_CONTRACTS_DIR
    shared_models_dir: str = DEFAULT_SHARED_MODELS_DIR

    @field_validator("contracts_dir", "shared_models_dir")
    @classmethod
    def _validate_non_empty_path(cls, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise ValueError(VALIDATION_MSG_NON_EMPTY_PATH)
        return value


class GeneratorConfig(BaseModel):
    model_config = _EXTRA_FORBID

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
            raise ValueError(VALIDATION_MSG_NON_EMPTY_PATH)
        if Path(candidate).is_absolute():
            raise ValueError(VALIDATION_MSG_ABSOLUTE_PATHS_NOT_ALLOWED)
        return value

    @field_validator("scaffold_dir")
    @classmethod
    def _validate_scaffold_dir(cls, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise ValueError(VALIDATION_MSG_NON_EMPTY_PATH)
        if Path(candidate).is_absolute():
            raise ValueError(VALIDATION_MSG_ABSOLUTE_PATHS_NOT_ALLOWED)
        return value

    @field_validator("scaffold_write_policy")
    @classmethod
    def _validate_scaffold_write_policy(cls, value: str) -> ScaffoldWritePolicy:
        candidate = value.strip().lower()
        if candidate not in SCAFFOLD_WRITE_POLICIES:
            raise ValueError(f"must be one of: {SCAFFOLD_WRITE_POLICIES_DISPLAY}")
        return cast(ScaffoldWritePolicy, candidate)


class TemplatesConfig(BaseModel):
    model_config = _EXTRA_FORBID

    dir: str = DEFAULT_TEMPLATES_DIR


class OpenAPIConfig(BaseModel):
    model_config = _EXTRA_FORBID

    include_extensions: bool = True


class EvolutionConfig(BaseModel):
    model_config = _EXTRA_FORBID

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
            raise ValueError(VALIDATION_MSG_NON_EMPTY_PATH)
        return value


class PathsConfig(BaseModel):
    model_config = _EXTRA_FORBID

    templates_dir: str = DEFAULT_TEMPLATES_DIR

    @field_validator("templates_dir")
    @classmethod
    def _validate_non_empty_templates_dir(cls, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise ValueError(VALIDATION_MSG_NON_EMPTY_PATH)
        return value


class ApidevConfig(BaseModel):
    model_config = _EXTRA_FORBID

    paths: PathsConfig = PathsConfig()
    inputs: InputsConfig = InputsConfig()
    generator: GeneratorConfig = GeneratorConfig()
    evolution: EvolutionConfig = EvolutionConfig()
    openapi: OpenAPIConfig = OpenAPIConfig()

    @property
    def contracts(self) -> ContractsConfig:
        return ContractsConfig(
            dir=self.inputs.contracts_dir,
            shared_models_dir=self.inputs.shared_models_dir,
        )

    @property
    def templates(self) -> TemplatesConfig:
        return TemplatesConfig(dir=self.paths.templates_dir)
