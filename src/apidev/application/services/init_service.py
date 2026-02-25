from pathlib import Path

from apidev.core.ports.filesystem import FileSystemPort

DEFAULT_CONFIG = """version = \"1\"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = "src/app/api/generated"

[templates]
dir = ".apidev/templates"
"""

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
    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    def run(self, project_dir: Path) -> int:
        created = 0
        apidev_dir = project_dir / ".apidev"
        contracts_dir = apidev_dir / "contracts"
        templates_dir = apidev_dir / "templates"

        for directory in (apidev_dir, contracts_dir, templates_dir):
            if not self.fs.exists(directory):
                self.fs.mkdir(directory, parents=True)
                created += 1

        config_path = apidev_dir / "config.toml"
        if not self.fs.exists(config_path):
            self.fs.write_text(config_path, DEFAULT_CONFIG)
            created += 1

        sample_contract = contracts_dir / "system" / "health.yaml"
        if not self.fs.exists(sample_contract):
            self.fs.mkdir(sample_contract.parent, parents=True)
            self.fs.write_text(sample_contract, DEFAULT_CONTRACT)
            created += 1

        return created
