from pathlib import Path

from apidev.application.dto.generation_plan import GenerateResult
from apidev.application.services.diff_service import DiffService
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.core.ports.writer import WriterPort


class GenerateService:
    def __init__(
        self,
        config_loader: ConfigLoaderPort,
        loader: ContractLoaderPort,
        renderer: TemplateEnginePort,
        fs: FileSystemPort,
        writer: WriterPort,
    ):
        self.diff_service = DiffService(
            config_loader=config_loader,
            loader=loader,
            renderer=renderer,
            fs=fs,
        )
        self.writer = writer

    def run(self, project_dir: Path, check: bool = False) -> GenerateResult:
        plan = self.diff_service.run(project_dir)
        changed = [c for c in plan.changes if c.change_type in {"ADD", "UPDATE"}]

        if check:
            return GenerateResult(applied_changes=0, drift_detected=bool(changed))

        for change in changed:
            self.writer.write(plan.generated_root, change.path, change.content)

        return GenerateResult(
            applied_changes=len(changed),
            drift_detected=False,
            changed_paths=[change.path for change in changed],
        )
