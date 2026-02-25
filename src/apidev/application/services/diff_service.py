from pathlib import Path

from apidev.application.dto.generation_plan import GenerationPlan, PlannedChange
from apidev.core.models.config import ApidevConfig
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.core.rules.operation_id import ensure_unique_operation_ids


class DiffService:
    def __init__(
        self,
        loader: ContractLoaderPort,
        renderer: TemplateEnginePort,
        fs: FileSystemPort,
    ):
        self.loader = loader
        self.renderer = renderer
        self.fs = fs

    def run(self, project_dir: Path) -> GenerationPlan:
        config = ApidevConfig.load(project_dir)
        generated_root = project_dir / config.generator.generated_dir

        operations = self.loader.load(project_dir)
        errors = ensure_unique_operation_ids(operations)
        if errors:
            raise ValueError("; ".join(errors))

        plan = GenerationPlan(generated_root=generated_root)

        operation_map_target = generated_root / "operation_map.py"
        operation_map_content = self.renderer.render(
            "generated_operation_map.py.j2", {"operations": operations}
        )
        plan.changes.append(self._planned_change(operation_map_target, operation_map_content))

        for op in operations:
            target = generated_root / "routers" / f"{op.operation_id}.py"
            content = self.renderer.render("generated_router.py.j2", {"operation": op})
            plan.changes.append(self._planned_change(target, content))

        return plan

    def _planned_change(self, target: Path, content: str) -> PlannedChange:
        if not self.fs.exists(target):
            return PlannedChange(path=target, content=content, change_type="ADD")

        current = self.fs.read_text(target)
        if current != content:
            return PlannedChange(path=target, content=content, change_type="UPDATE")

        return PlannedChange(path=target, content=content, change_type="SAME")
