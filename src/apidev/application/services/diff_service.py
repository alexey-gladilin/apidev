from pathlib import Path

from apidev.application.dto.resolved_paths import resolve_paths
from apidev.application.dto.generation_plan import GenerationPlan, PlannedChange
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.core.rules.operation_id import ensure_unique_operation_ids


class DiffService:
    def __init__(
        self,
        config_loader: ConfigLoaderPort,
        loader: ContractLoaderPort,
        renderer: TemplateEnginePort,
        fs: FileSystemPort,
    ):
        self.config_loader = config_loader
        self.loader = loader
        self.renderer = renderer
        self.fs = fs

    def run(self, project_dir: Path) -> GenerationPlan:
        config = self.config_loader.load(project_dir)
        paths = resolve_paths(project_dir, config)

        operations = self.loader.load(paths.contracts_dir)
        errors = ensure_unique_operation_ids(operations)
        if errors:
            raise ValueError("; ".join(errors))

        plan = GenerationPlan(generated_root=paths.generated_root)

        operation_map_target = paths.generated_root / "operation_map.py"
        operation_map_content = self.renderer.render(
            "generated_operation_map.py.j2", {"operations": operations}
        )
        plan.changes.append(self._planned_change(operation_map_target, operation_map_content))

        for op in operations:
            target = paths.generated_root / "routers" / f"{op.operation_id}.py"
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
