import json
from pathlib import Path
import tomllib

import tomli_w
from pydantic import ValidationError

from apidev.core.models.config import ApidevConfig
from apidev.core.models.release_state import ReleaseState
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.filesystem import FileSystemPort

MAX_RELEASE_STATE_FILE_SIZE_BYTES = 1024 * 1024


def default_config_text() -> str:
    return tomli_w.dumps(ApidevConfig().model_dump())


class TomlConfigLoader(ConfigLoaderPort):
    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    def load(self, project_dir: Path) -> ApidevConfig:
        path = project_dir / ".apidev" / "config.toml"
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

        try:
            return ReleaseState.model_validate(data)
        except ValidationError as exc:
            raise ValueError(self._format_validation_error(path, exc)) from exc

    def _resolve_path(self, project_dir: Path, raw_path: str) -> Path:
        project_root = project_dir.resolve()
        candidate = Path(raw_path)
        if candidate.is_absolute():
            raise ValueError(
                f"Invalid release state path '{raw_path}': absolute paths are not allowed"
            )

        resolved = (project_root / candidate).resolve(strict=False)
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(
                f"Invalid release state path '{raw_path}': path must stay inside project directory '{project_root}'"
            ) from exc
        return resolved

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
            location = ".".join(str(item) for item in error.get("loc", [])) or "<root>"
            message = str(error.get("msg", "invalid value"))
            parts.append(f"{location}: {message}")
        details = "; ".join(parts)
        return f"Invalid configuration in '{path}': {details}"
