from pathlib import Path

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

    def run(self, project_dir: Path) -> int:
        paths = resolve_paths(project_dir, ApidevConfig())
        created = 0

        for directory in (paths.apidev_dir, paths.contracts_dir, paths.templates_dir):
            if not self.fs.exists(directory):
                self.fs.mkdir(directory, parents=True)
                created += 1

        if not self.fs.exists(paths.config_path):
            self.fs.write_text(paths.config_path, self.default_config_text)
            created += 1

        sample_contract = paths.contracts_dir / "system" / "health.yaml"
        if not self.fs.exists(sample_contract):
            self.fs.mkdir(sample_contract.parent, parents=True)
            self.fs.write_text(sample_contract, DEFAULT_CONTRACT)
            created += 1

        return created
