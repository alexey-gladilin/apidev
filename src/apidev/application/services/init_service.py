from pathlib import Path
from dataclasses import dataclass
from importlib import resources
from typing import Literal
import tomllib

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
        config_path = project_dir / ".apidev" / "config.toml"
        existing_config = self._load_existing_config(config_path)

        if mode == "force":
            paths = resolve_paths(project_dir, ApidevConfig())
        else:
            paths = resolve_paths(project_dir, existing_config or ApidevConfig())

        changed = 0
        invalid_paths: list[Path] = []

        for directory in (paths.apidev_dir, paths.contracts_dir, paths.templates_dir):
            if not self.fs.exists(directory):
                self.fs.mkdir(directory, parents=True)
                changed += 1

        sample_contract = paths.contracts_dir / "system" / "health.yaml"
        managed_templates = self._load_managed_templates()

        managed_defaults = {
            paths.config_path: self.default_config_text,
            sample_contract: DEFAULT_CONTRACT,
        }
        for template_name, template_content in managed_templates.items():
            managed_defaults[paths.templates_dir / template_name] = template_content

        for file_path, default_content in managed_defaults.items():
            if self.fs.exists(file_path):
                if file_path == paths.config_path:
                    if self._load_existing_config(file_path) is None:
                        invalid_paths.append(file_path)
                    continue

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

    def _load_existing_config(self, config_path: Path) -> ApidevConfig | None:
        if not self.fs.exists(config_path):
            return None

        try:
            raw = self.fs.read_text(config_path)
            data = tomllib.loads(raw)
            return ApidevConfig.model_validate(data)
        except (tomllib.TOMLDecodeError, ValueError):
            return None

    def _load_managed_templates(self) -> dict[str, str]:
        template_files = (
            "generated_operation_map.py.j2",
            "generated_openapi_docs.py.j2",
            "generated_router.py.j2",
            "generated_schema.py.j2",
        )
        templates_root = resources.files("apidev").joinpath("templates")
        managed: dict[str, str] = {}
        for template_name in template_files:
            managed[template_name] = templates_root.joinpath(template_name).read_text(
                encoding="utf-8"
            )
        return managed


@dataclass(slots=True)
class InitResult:
    status: Literal["initialized", "already_initialized", "repaired", "forced"]
    changed: int


class InitRepairRequiredError(ValueError):
    def __init__(self, invalid_paths: list[Path]):
        super().__init__("Project has invalid init-managed file(s).")
        self.invalid_paths = invalid_paths
