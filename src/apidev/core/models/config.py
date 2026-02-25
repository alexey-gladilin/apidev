from pydantic import BaseModel


class ContractsConfig(BaseModel):
    dir: str = ".apidev/contracts"


class GeneratorConfig(BaseModel):
    generated_dir: str = "output/api"


class TemplatesConfig(BaseModel):
    dir: str = ".apidev/templates"


class ApidevConfig(BaseModel):
    version: str = "1"
    contracts: ContractsConfig = ContractsConfig()
    generator: GeneratorConfig = GeneratorConfig()
    templates: TemplatesConfig = TemplatesConfig()
