from pathlib import Path
from dataclasses import dataclass
from typing import Literal

from apidev.application.dto.resolved_paths import resolve_paths
from apidev.core.models.config import ApidevConfig
from apidev.core.ports.filesystem import FileSystemPort

DEFAULT_CONTRACT = """method: GET
path: /v1/health
auth: public
summary: Health endpoint
description: Returns health status.
response:
  status: 200
  body:
    type: object
    properties:
      status:
        type: string
        required: true
errors:
  - code: INTERNAL_ERROR
    http_status: 500
    body:
      type: object
      properties:
        error_code:
          type: string
          required: true
        message:
          type: string
          required: true
"""


class InitService:
    def __init__(self, fs: FileSystemPort, default_config_text: str):
        self.fs = fs
        self.default_config_text = default_config_text

    def run(
        self, project_dir: Path, mode: Literal["create", "repair", "force"] = "create"
    ) -> "InitResult":
        paths = resolve_paths(project_dir, ApidevConfig())
        changed = 0
        invalid_paths: list[Path] = []

        for directory in (paths.apidev_dir, paths.contracts_dir, paths.templates_dir):
            if not self.fs.exists(directory):
                self.fs.mkdir(directory, parents=True)
                changed += 1

        sample_contract = paths.contracts_dir / "system" / "health.yaml"

        managed_defaults = {
            paths.config_path: self.default_config_text,
            sample_contract: DEFAULT_CONTRACT,
        }

        for file_path, default_content in managed_defaults.items():
            if self.fs.exists(file_path):
                current = self.fs.read_text(file_path)
                if current != default_content:
                    invalid_paths.append(file_path)
            else:
                self.fs.mkdir(file_path.parent, parents=True)
                self.fs.write_text(file_path, default_content)
                changed += 1

        if mode == "create":
            if invalid_paths:
                raise InitRepairRequiredError(invalid_paths=invalid_paths)
            status = "already_initialized" if changed == 0 else "initialized"
            return InitResult(status=status, changed=changed)

        if mode == "repair":
            for file_path in invalid_paths:
                self.fs.write_text(file_path, managed_defaults[file_path])
                changed += 1
            return InitResult(status="repaired", changed=changed)

        for file_path, default_content in managed_defaults.items():
            self.fs.write_text(file_path, default_content)
        return InitResult(status="forced", changed=changed + len(managed_defaults))


@dataclass(slots=True)
class InitResult:
    status: Literal["initialized", "already_initialized", "repaired", "forced"]
    changed: int


class InitRepairRequiredError(ValueError):
    def __init__(self, invalid_paths: list[Path]):
        super().__init__("Project has invalid init-managed file(s).")
        self.invalid_paths = invalid_paths
