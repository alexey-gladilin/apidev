from pathlib import Path
import tomllib

from pydantic import BaseModel


class ContractsConfig(BaseModel):
    dir: str = ".apidev/contracts"


class GeneratorConfig(BaseModel):
    generated_dir: str = "src/app/api/generated"


class TemplatesConfig(BaseModel):
    dir: str = ".apidev/templates"


class ApidevConfig(BaseModel):
    version: str = "1"
    contracts: ContractsConfig = ContractsConfig()
    generator: GeneratorConfig = GeneratorConfig()
    templates: TemplatesConfig = TemplatesConfig()

    @classmethod
    def load(cls, project_dir: Path) -> "ApidevConfig":
        path = project_dir / ".apidev" / "config.toml"
        if not path.exists():
            return cls()

        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)
