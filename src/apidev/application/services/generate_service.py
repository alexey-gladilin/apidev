from pathlib import Path

from apidev.application.dto.generation_plan import (
    CompatibilityPolicy,
    GenerateResult,
    GenerationDiagnostic,
)
from apidev.application.services.diff_service import DiffService
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.python_postprocessor import PythonPostprocessorPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.core.ports.writer import WriterPort


class GenerateService:
    _REMOVE_CONFLICT_CODE = "remove-conflict"
    _REMOVE_BOUNDARY_VIOLATION_CODE = "remove-boundary-violation"

    def __init__(
        self,
        config_loader: ConfigLoaderPort,
        loader: ContractLoaderPort,
        renderer: TemplateEnginePort,
        fs: FileSystemPort,
        writer: WriterPort,
        postprocessor: PythonPostprocessorPort,
    ):
        self.diff_service = DiffService(
            config_loader=config_loader,
            loader=loader,
            renderer=renderer,
            fs=fs,
            postprocessor=postprocessor,
        )
        self.writer = writer

    def run(
        self,
        project_dir: Path,
        check: bool = False,
        compatibility_policy: CompatibilityPolicy = "warn",
        baseline_ref: str | None = None,
        scaffold: bool | None = None,
    ) -> GenerateResult:
        plan = self.diff_service.run(
            project_dir,
            compatibility_policy=compatibility_policy,
            baseline_ref=baseline_ref,
            scaffold=scaffold,
        )
        drift_changes = [c for c in plan.changes if c.change_type in {"ADD", "UPDATE", "REMOVE"}]
        writable_changes = [c for c in plan.changes if c.change_type in {"ADD", "UPDATE"}]
        removable_changes = [c for c in plan.changes if c.change_type == "REMOVE"]

        if check:
            return GenerateResult(
                applied_changes=0,
                drift_status="drift" if drift_changes else "no-drift",
                compatibility_policy=plan.compatibility_policy,
                compatibility=plan.compatibility,
                policy_blocked=plan.policy_blocked,
            )

        for change in writable_changes:
            self.writer.write(plan.generated_root, change.path, change.content)

        removed_paths: list[Path] = []
        changed_paths = [change.path for change in writable_changes]
        for change in removable_changes:
            try:
                removed = self._remove_generated_artifact(plan.generated_root, change.path)
            except ValueError as exc:
                changed_paths.extend(removed_paths)
                return GenerateResult(
                    applied_changes=len(changed_paths),
                    drift_status="error",
                    changed_paths=changed_paths,
                    diagnostics=[self._remove_diagnostic(change.path, error=exc)],
                    compatibility_policy=plan.compatibility_policy,
                    compatibility=plan.compatibility,
                    policy_blocked=plan.policy_blocked,
                )
            if not removed:
                changed_paths.extend(removed_paths)
                return GenerateResult(
                    applied_changes=len(changed_paths),
                    drift_status="error",
                    changed_paths=changed_paths,
                    diagnostics=[self._remove_diagnostic(change.path, error=None)],
                    compatibility_policy=plan.compatibility_policy,
                    compatibility=plan.compatibility,
                    policy_blocked=plan.policy_blocked,
                )
            removed_paths.append(change.path)

        changed_paths.extend(removed_paths)

        return GenerateResult(
            applied_changes=len(changed_paths),
            drift_status="no-drift",
            changed_paths=changed_paths,
            compatibility_policy=plan.compatibility_policy,
            compatibility=plan.compatibility,
            policy_blocked=plan.policy_blocked,
        )

    def _remove_generated_artifact(self, generated_root: Path, target: Path) -> bool:
        # Backward-compatible hook for integration tests that monkeypatch remove failures.
        return self.writer.remove(generated_root, target)

    def _remove_diagnostic(
        self,
        target: Path,
        error: ValueError | None,
    ) -> GenerationDiagnostic:
        location = target.as_posix()
        if error is None:
            return GenerationDiagnostic(
                code=self._REMOVE_CONFLICT_CODE,
                location=location,
                detail="stale artifact is missing at apply time",
            )

        detail = str(error).strip() or "remove apply failed"
        if self._is_remove_boundary_violation(detail):
            return GenerationDiagnostic(
                code=self._REMOVE_BOUNDARY_VIOLATION_CODE,
                location=location,
                detail=detail,
            )
        return GenerationDiagnostic(
            code=self._REMOVE_CONFLICT_CODE,
            location=location,
            detail=detail,
        )

    def _is_remove_boundary_violation(self, detail: str) -> bool:
        return "outside generated root" in detail or "generated root path directly" in detail
