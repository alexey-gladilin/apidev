from typing import Any, Protocol


class TemplateEnginePort(Protocol):
    def render(self, template_name: str, context: dict[str, Any]) -> str: ...
