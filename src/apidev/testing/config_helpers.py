from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apidev.core.constants import (
    APIDEV_CONFIG_FILENAME,
    APIDEV_DIRNAME,
    DEFAULT_RELEASE_STATE_FILE,
)

CONFIG_DIRNAME = APIDEV_DIRNAME
CONFIG_FILENAME = APIDEV_CONFIG_FILENAME
DEFAULT_RELEASE_STATE_RELATIVE_PATH = Path(DEFAULT_RELEASE_STATE_FILE)
INIT_INVALID_MANAGED_FILES_MESSAGE = "Project has invalid init-managed file(s)."


def write_config(project_dir: Path, toml_text: str) -> None:
    (project_dir / CONFIG_DIRNAME).mkdir(parents=True, exist_ok=True)
    (project_dir / CONFIG_DIRNAME / CONFIG_FILENAME).write_text(
        toml_text.strip() + "\n",
        encoding="utf-8",
    )


def write_release_state(
    project_dir: Path,
    payload: dict[str, Any],
    *,
    relative_path: Path = DEFAULT_RELEASE_STATE_RELATIVE_PATH,
) -> Path:
    target = project_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return target
