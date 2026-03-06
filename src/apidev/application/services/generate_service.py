from pathlib import Path
import json
import subprocess

from apidev.application.dto.generation_plan import (
    CompatibilityPolicy,
    EndpointFilters,
    GenerateResult,
    GenerationDiagnostic,
)
from apidev.application.services.diff_service import DiffService
from apidev.core.constants import DEFAULT_COMPATIBILITY_POLICY
from apidev.core.models.release_state import validate_baseline_ref
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.python_postprocessor import PythonPostprocessorPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.core.ports.writer import WriterPort


class GenerateService:
    _REMOVE_CONFLICT_CODE = "generation.remove-conflict"
    _REMOVE_BOUNDARY_VIOLATION_CODE = "generation.remove-boundary-violation"
    _BASELINE_MISSING_CODE = "config.baseline-missing"
    _BASELINE_INVALID_CODE = "config.baseline-invalid"
    _RELEASE_STATE_APPLY_FAILED_CODE = "config.release-state-apply-failed"

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
        self.config_loader = config_loader
        self.fs = fs
        self.writer = writer

    def run(
        self,
        project_dir: Path,
        check: bool = False,
        compatibility_policy: CompatibilityPolicy = DEFAULT_COMPATIBILITY_POLICY,
        baseline_ref: str | None = None,
        scaffold: bool | None = None,
        endpoint_filters: EndpointFilters | None = None,
    ) -> GenerateResult:
        plan = self.diff_service.run(
            project_dir,
            compatibility_policy=compatibility_policy,
            baseline_ref=baseline_ref,
            scaffold=scaffold,
            endpoint_filters=endpoint_filters,
        )
        if plan.diagnostics:
            return GenerateResult(
                applied_changes=0,
                drift_status="error",
                diagnostics=list(plan.diagnostics),
                compatibility_policy=plan.compatibility_policy,
                compatibility=plan.compatibility,
                policy_blocked=plan.policy_blocked,
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

        apply_baseline_diagnostic = self._resolve_apply_baseline_diagnostic(
            project_dir=project_dir,
            baseline_ref=baseline_ref,
        )
        if apply_baseline_diagnostic is not None:
            return GenerateResult(
                applied_changes=0,
                drift_status="error",
                changed_paths=[],
                diagnostics=[
                    GenerationDiagnostic(
                        code=apply_baseline_diagnostic,
                        location="baseline",
                    )
                ],
                compatibility_policy=plan.compatibility_policy,
                compatibility=plan.compatibility,
                policy_blocked=plan.policy_blocked,
            )

        boundary_root = project_dir
        for change in writable_changes:
            self.writer.write(boundary_root, change.path, change.content)

        removed_paths: list[Path] = []
        changed_paths = [change.path for change in writable_changes]
        for change in removable_changes:
            try:
                removed = self._remove_generated_artifact(boundary_root, change.path)
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
        release_state_existed_before_apply = self._has_configured_release_state(project_dir)
        release_state_snapshot = self._snapshot_release_state(project_dir)
        try:
            self._auto_create_release_state_if_missing(
                project_dir=project_dir,
                baseline_ref=baseline_ref,
            )
            self._sync_release_state_baseline_ref(
                project_dir=project_dir,
                baseline_ref=baseline_ref,
            )
            self._bump_release_number_if_needed(
                project_dir=project_dir,
                has_applied_changes=bool(changed_paths),
                release_state_existed_before_apply=release_state_existed_before_apply,
            )
        except OSError as exc:
            self._restore_release_state_snapshot(release_state_snapshot)
            return GenerateResult(
                applied_changes=len(changed_paths),
                drift_status="error",
                changed_paths=changed_paths,
                diagnostics=[
                    GenerationDiagnostic(
                        code=self._RELEASE_STATE_APPLY_FAILED_CODE,
                        location="release-state",
                        detail=str(exc).strip() or "release-state apply failed",
                    )
                ],
                compatibility_policy=plan.compatibility_policy,
                compatibility=plan.compatibility,
                policy_blocked=plan.policy_blocked,
            )

        return GenerateResult(
            applied_changes=len(changed_paths),
            drift_status="no-drift",
            changed_paths=changed_paths,
            compatibility_policy=plan.compatibility_policy,
            compatibility=plan.compatibility,
            policy_blocked=plan.policy_blocked,
        )

    def _remove_generated_artifact(self, generated_dir_path: Path, target: Path) -> bool:
        # Backward-compatible hook for integration tests that monkeypatch remove failures.
        return self.writer.remove(generated_dir_path, target)

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

    def _auto_create_release_state_if_missing(
        self,
        project_dir: Path,
        baseline_ref: str | None,
    ) -> None:
        config = self.config_loader.load(project_dir)
        release_state_path = self._resolve_release_state_path(
            project_dir=project_dir,
            raw_path=config.evolution.release_state_file,
        )
        if release_state_path is None or self.fs.exists(release_state_path):
            return

        resolved_baseline_ref = self._resolve_baseline_ref_for_release_state_bootstrap(
            project_dir=project_dir,
            baseline_ref=baseline_ref,
        )
        if resolved_baseline_ref is None:
            return

        payload = {
            "release_number": 1,
            "baseline_ref": resolved_baseline_ref,
        }
        self.fs.write_text(release_state_path, json.dumps(payload))

    def _sync_release_state_baseline_ref(
        self,
        project_dir: Path,
        baseline_ref: str | None,
    ) -> None:
        config = self.config_loader.load(project_dir)
        release_state_path = self._resolve_release_state_path(
            project_dir=project_dir,
            raw_path=config.evolution.release_state_file,
        )
        if release_state_path is None or not self.fs.exists(release_state_path):
            return

        try:
            payload = json.loads(self.fs.read_text(release_state_path))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return

        release_state_baseline_ref = payload.get("baseline_ref")
        resolved_baseline_ref = self._resolve_baseline_ref_for_release_state_sync(
            project_dir=project_dir,
            baseline_ref=baseline_ref,
            release_state_baseline_ref=release_state_baseline_ref,
        )
        if resolved_baseline_ref is None or payload.get("baseline_ref") == resolved_baseline_ref:
            return

        payload["baseline_ref"] = resolved_baseline_ref
        self.fs.write_text(release_state_path, json.dumps(payload))

    def _has_configured_release_state(self, project_dir: Path) -> bool:
        config = self.config_loader.load(project_dir)
        release_state_path = self._resolve_release_state_path(
            project_dir=project_dir,
            raw_path=config.evolution.release_state_file,
        )
        if release_state_path is None:
            return False
        return self.fs.exists(release_state_path)

    def _snapshot_release_state(
        self,
        project_dir: Path,
    ) -> tuple[Path | None, bool, str | None]:
        config = self.config_loader.load(project_dir)
        release_state_path = self._resolve_release_state_path(
            project_dir=project_dir,
            raw_path=config.evolution.release_state_file,
        )
        if release_state_path is None:
            return (None, False, None)
        if not self.fs.exists(release_state_path):
            return (release_state_path, False, None)
        try:
            return (release_state_path, True, self.fs.read_text(release_state_path))
        except OSError:
            return (release_state_path, True, None)

    def _restore_release_state_snapshot(
        self,
        snapshot: tuple[Path | None, bool, str | None],
    ) -> None:
        release_state_path, existed_before_run, content_before_run = snapshot
        if release_state_path is None:
            return

        try:
            exists_now = self.fs.exists(release_state_path)
        except OSError:
            return

        if not existed_before_run:
            if exists_now:
                try:
                    release_state_path.unlink(missing_ok=True)
                except OSError:
                    return
            return

        if content_before_run is None:
            return

        try:
            self.fs.write_text(release_state_path, content_before_run)
        except OSError:
            return

    def _bump_release_number_if_needed(
        self,
        project_dir: Path,
        has_applied_changes: bool,
        release_state_existed_before_apply: bool,
    ) -> None:
        if not has_applied_changes or not release_state_existed_before_apply:
            return

        config = self.config_loader.load(project_dir)
        release_state_path = self._resolve_release_state_path(
            project_dir=project_dir,
            raw_path=config.evolution.release_state_file,
        )
        if release_state_path is None or not self.fs.exists(release_state_path):
            return

        try:
            payload = json.loads(self.fs.read_text(release_state_path))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return

        release_number = payload.get("release_number")
        if not isinstance(release_number, int) or release_number < 1:
            return

        payload["release_number"] = release_number + 1
        self.fs.write_text(release_state_path, json.dumps(payload))

    def _resolve_release_state_path(self, project_dir: Path, raw_path: str) -> Path | None:
        project_root = project_dir.resolve()
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return None

        resolved = (project_root / candidate).resolve(strict=False)
        try:
            resolved.relative_to(project_root)
        except ValueError:
            return None
        return resolved

    def _resolve_baseline_ref_for_release_state_bootstrap(
        self,
        project_dir: Path,
        baseline_ref: str | None,
    ) -> str | None:
        return self._resolve_baseline_ref_for_release_state_sync(
            project_dir=project_dir,
            baseline_ref=baseline_ref,
            release_state_baseline_ref=None,
        )

    def _resolve_baseline_ref_for_release_state_sync(
        self,
        project_dir: Path,
        baseline_ref: str | None,
        release_state_baseline_ref: object | None,
    ) -> str | None:
        if baseline_ref is not None:
            try:
                return validate_baseline_ref(baseline_ref)
            except ValueError:
                return None

        if isinstance(release_state_baseline_ref, str):
            try:
                return validate_baseline_ref(release_state_baseline_ref)
            except ValueError:
                pass

        head_ref = self._run_git_command(
            project_dir=project_dir, args=("rev-parse", "--verify", "HEAD")
        )
        if head_ref is None:
            return None

        try:
            return validate_baseline_ref(head_ref)
        except ValueError:
            return None

    def _resolve_apply_baseline_diagnostic(
        self,
        project_dir: Path,
        baseline_ref: str | None,
    ) -> str | None:
        baseline_invalid = False
        if baseline_ref is not None:
            try:
                validate_baseline_ref(baseline_ref)
                return None
            except ValueError:
                return self._BASELINE_INVALID_CODE

        config = self.config_loader.load(project_dir)
        release_state_path = self._resolve_release_state_path(
            project_dir=project_dir,
            raw_path=config.evolution.release_state_file,
        )
        if release_state_path is not None and self.fs.exists(release_state_path):
            try:
                payload = json.loads(self.fs.read_text(release_state_path))
            except (OSError, json.JSONDecodeError):
                baseline_invalid = True
            else:
                if isinstance(payload, dict):
                    release_state_baseline_ref = payload.get("baseline_ref")
                    if release_state_baseline_ref is None:
                        pass
                    elif isinstance(release_state_baseline_ref, str):
                        try:
                            validate_baseline_ref(release_state_baseline_ref)
                            return None
                        except ValueError:
                            baseline_invalid = True
                    else:
                        baseline_invalid = True
                else:
                    baseline_invalid = True

        head_ref = self._run_git_command(
            project_dir=project_dir, args=("rev-parse", "--verify", "HEAD")
        )
        if head_ref is None:
            return self._BASELINE_INVALID_CODE if baseline_invalid else self._BASELINE_MISSING_CODE

        try:
            validate_baseline_ref(head_ref)
        except ValueError:
            return self._BASELINE_INVALID_CODE
        return None

    def _run_git_command(self, project_dir: Path, args: tuple[str, ...]) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=project_dir,
                check=False,
                text=True,
                capture_output=True,
            )
        except (FileNotFoundError, OSError):
            return None
        if completed.returncode != 0:
            return None
        return completed.stdout.strip() or None
