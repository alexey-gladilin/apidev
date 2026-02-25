from pathlib import Path
from typing import Any

from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    select_autoescape,
)

from apidev.core.ports.template_engine import TemplateEnginePort


class JinjaTemplateRenderer(TemplateEnginePort):
    def __init__(self, project_dir: Path | None = None):
        loaders: list[PackageLoader | FileSystemLoader] = [PackageLoader("apidev", "templates")]
        if project_dir is not None:
            custom_templates = project_dir / ".apidev" / "templates"
            loaders.insert(0, FileSystemLoader(str(custom_templates)))

        self.env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context).rstrip() + "\n"
