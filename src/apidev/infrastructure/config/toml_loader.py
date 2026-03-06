import json
from pathlib import Path
import tomllib
from typing import Any

import tomli_w
from pydantic import ValidationError

from apidev.core.constants import (
    APIDEV_CONFIG_RELATIVE_PATH,
    DIAG_CODE_PATH_BOUNDARY_VIOLATION,
    DIAG_CODE_RELEASE_STATE_INVALID_KEY,
    DIAG_CODE_RELEASE_STATE_TYPE_MISMATCH,
    DIAG_FIELD_ERROR_CODE,
    DIAG_FIELD_KEY_PATH,
    DIAG_FIELD_PROJECT_DIR,
    DIAG_FIELD_RESOLVED_PATH,
    DIAG_KEY_PATH_EVOLUTION_RELEASE_STATE_FILE,
)
from apidev.core.models.config import ApidevConfig
from apidev.core.models.release_state import ReleaseState
from apidev.core.path_boundary import is_path_within_root
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.filesystem import FileSystemPort

MAX_RELEASE_STATE_FILE_SIZE_BYTES = 1024 * 1024
_ROOT_KEY_PATH = "<root>"


def default_config_text() -> str:
    return tomli_w.dumps(ApidevConfig().model_dump())


class TomlConfigLoader(ConfigLoaderPort):
    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    def load(self, project_dir: Path) -> ApidevConfig:
        path = project_dir / APIDEV_CONFIG_RELATIVE_PATH
        if not self.fs.exists(path):
            return ApidevConfig()

        try:
            data = tomllib.loads(self.fs.read_text(path))
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"Invalid config file '{path}': {exc}") from exc

        try:
            return ApidevConfig.model_validate(data)
        except ValidationError as exc:
            raise ValueError(self._format_validation_error(path, exc)) from exc

    def load_release_state(self, project_dir: Path, config: ApidevConfig) -> ReleaseState:
        path = self._resolve_path(project_dir, config.evolution.release_state_file)

        if not self.fs.exists(path):
            raise ValueError(f"Release state file not found: {path}")
        self._validate_release_state_file_size(path)

        raw = self.fs.read_text(path)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid release state JSON '{path}': {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Invalid release state '{path}': expected a JSON object")

        if "current_release" in data:
            raise ValueError(
                self._build_release_state_diagnostic_payload(
                    code=DIAG_CODE_RELEASE_STATE_INVALID_KEY,
                    message="release-state contains unsupported legacy key",
                    context={"field": "current_release"},
                )
            )
        if "release_number" in data and not self._is_strict_positive_int_type(
            data["release_number"]
        ):
            raise ValueError(
                self._build_release_state_diagnostic_payload(
                    code=DIAG_CODE_RELEASE_STATE_TYPE_MISMATCH,
                    message="release-state field has invalid type",
                    context={
                        "field": "release_number",
                        "expected_type": "int",
                        "actual_type": type(data["release_number"]).__name__,
                    },
                )
            )

        try:
            return ReleaseState.model_validate(data)
        except ValidationError as exc:
            raise ValueError(self._format_validation_error(path, exc)) from exc

    def _resolve_path(self, project_dir: Path, raw_path: str) -> Path:
        project_root = project_dir.resolve(strict=False)
        candidate = Path(raw_path)
        resolved_candidate = self._resolve_candidate_path(project_root, candidate)

        if candidate.is_absolute() or not is_path_within_root(resolved_candidate, project_root):
            raise ValueError(
                self._build_path_boundary_diagnostic_payload(
                    key_path=DIAG_KEY_PATH_EVOLUTION_RELEASE_STATE_FILE,
                    resolved_path=resolved_candidate,
                    project_dir=project_root,
                )
            )
        return resolved_candidate

    def _resolve_candidate_path(self, project_root: Path, candidate: Path) -> Path:
        if candidate.is_absolute():
            return candidate.resolve(strict=False)
        return (project_root / candidate).resolve(strict=False)

    def _validate_release_state_file_size(self, path: Path) -> None:
        size_bytes = path.stat().st_size
        if size_bytes > MAX_RELEASE_STATE_FILE_SIZE_BYTES:
            raise ValueError(
                f"Release state file '{path}' exceeds max size "
                f"{MAX_RELEASE_STATE_FILE_SIZE_BYTES} bytes"
            )

    def _format_validation_error(self, path: Path, exc: ValidationError) -> str:
        parts: list[str] = []
        for error in exc.errors():
            location = ".".join(str(item) for item in error.get("loc", [])) or _ROOT_KEY_PATH
            message = str(error.get("msg", "invalid value"))
            parts.append(f"key_path={location}: {message}")
        parts.sort()
        details = "; ".join(parts)
        return f"Invalid configuration in '{path}': {details}"

    def _build_release_state_diagnostic_payload(
        self,
        *,
        code: str,
        message: str,
        context: dict[str, Any],
    ) -> str:
        payload = {
            "code": code,
            "message": message,
            "context": context,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _build_path_boundary_diagnostic_payload(
        self,
        *,
        key_path: str,
        resolved_path: Path,
        project_dir: Path,
    ) -> str:
        payload = {
            DIAG_FIELD_ERROR_CODE: DIAG_CODE_PATH_BOUNDARY_VIOLATION,
            DIAG_FIELD_KEY_PATH: key_path,
            DIAG_FIELD_PROJECT_DIR: project_dir.as_posix(),
            DIAG_FIELD_RESOLVED_PATH: resolved_path.as_posix(),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _is_strict_positive_int_type(self, value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)
