import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import cast

import yaml
from apidev.application.dto.resolved_paths import resolve_paths
from apidev.application.dto.generation_plan import (
    CompatibilityDiagnostic,
    CompatibilityPolicy,
    CompatibilitySummary,
    GenerationPlan,
    PlannedChange,
)
from apidev.core.models.baseline_snapshot import BaselineSnapshot
from apidev.core.models.contract import EndpointContract
from apidev.core.models.release_state import validate_baseline_ref
from apidev.core.models.operation import Operation
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.python_postprocessor import PythonPostprocessMode, PythonPostprocessorPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.core.rules.compatibility import (
    CompatibilityChange,
    CompatibilityCategory,
    classify_changes,
)
from apidev.core.rules.operation_id import build_operation_id, ensure_unique_operation_ids


class DiffService:
    _MAX_HINT_RECURSION_DEPTH = 64
    _BASELINE_CACHE_RELATIVE_ROOT = Path(".apidev") / "cache" / "baseline"
    _MAX_BASELINE_CACHE_SIZE_BYTES = 5_000_000
    _SCAFFOLD_TEMPLATES: tuple[tuple[str, str], ...] = (
        ("handler_registry.py", "integration_handler_registry.py.j2"),
        ("router_factory.py", "integration_router_factory.py.j2"),
        ("auth_registry.py", "integration_auth_registry.py.j2"),
        ("error_mapper.py", "integration_error_mapper.py.j2"),
    )

    def __init__(
        self,
        config_loader: ConfigLoaderPort,
        loader: ContractLoaderPort,
        renderer: TemplateEnginePort,
        fs: FileSystemPort,
        postprocessor: PythonPostprocessorPort,
    ):
        self.config_loader = config_loader
        self.loader = loader
        self.renderer = renderer
        self.fs = fs
        self.postprocessor = postprocessor

    def run(
        self,
        project_dir: Path,
        compatibility_policy: CompatibilityPolicy = "warn",
        baseline_ref: str | None = None,
        scaffold: bool | None = None,
    ) -> GenerationPlan:
        normalized_policy = self._normalize_policy(compatibility_policy)
        config = self.config_loader.load(project_dir)
        paths = resolve_paths(project_dir, config)
        postprocess_mode = config.generator.postprocess
        effective_scaffold = config.generator.scaffold if scaffold is None else scaffold
        scaffold_root = self._resolve_scaffold_root(
            generated_root=paths.generated_root,
            raw_scaffold_dir=config.generator.scaffold_dir,
        )

        operations = self.loader.load(paths.contracts_dir)
        errors = ensure_unique_operation_ids(operations)
        if errors:
            raise ValueError("; ".join(errors))
        ordered_operations = sorted(operations, key=lambda op: op.operation_id)
        enriched_operations = ordered_operations
        transport_segments = self._build_transport_segment_index(enriched_operations)

        release_number: int | None = None
        deprecated_operations: dict[str, int] = {}
        release_state_error = ""
        release_state_baseline_ref: str | None = None
        try:
            release_state = self.config_loader.load_release_state(project_dir, config)
            release_number = release_state.release_number
            release_state_baseline_ref = release_state.baseline_ref
            deprecated_operations = dict(release_state.deprecated_operations)
        except ValueError as exc:
            release_state_error = str(exc)

        plan = GenerationPlan(generated_root=paths.generated_root)

        registry_entries = [
            self._build_registry_entry(op, deprecated_operations, transport_segments)
            for op in enriched_operations
        ]
        operation_map_target = paths.generated_root / "operation_map.py"
        operation_map_content = self.renderer.render(
            "generated_operation_map.py.j2",
            {
                "operations": enriched_operations,
                "registry_entries": registry_entries,
            },
        )
        operation_map_content = self._postprocess_python(
            project_dir, operation_map_target, operation_map_content, postprocess_mode
        )
        plan.changes.append(self._planned_change(operation_map_target, operation_map_content))

        openapi_docs_target = paths.generated_root / "openapi_docs.py"
        openapi_docs_content = self.renderer.render(
            "generated_openapi_docs.py.j2",
            {
                "registry_entries": registry_entries,
            },
        )
        openapi_docs_content = self._postprocess_python(
            project_dir, openapi_docs_target, openapi_docs_content, postprocess_mode
        )
        plan.changes.append(self._planned_change(openapi_docs_target, openapi_docs_content))

        for domain_segment in sorted({segments[0] for segments in transport_segments.values()}):
            for package_suffix in ("", "routes", "models"):
                package_dir = paths.generated_root / domain_segment
                if package_suffix:
                    package_dir = package_dir / package_suffix
                init_target = package_dir / "__init__.py"
                init_content = self._postprocess_python(
                    project_dir=project_dir,
                    target=init_target,
                    content=self._generated_package_init_content(
                        domain_segment=domain_segment,
                        package_suffix=package_suffix,
                    ),
                    mode=postprocess_mode,
                )
                plan.changes.append(self._planned_change(init_target, init_content))

        for op in enriched_operations:
            domain_segment, operation_segment = transport_segments[op.operation_id]
            bridge_contract = self._build_bridge_contract(
                op, deprecated_operations, transport_segments
            )
            target = paths.generated_root / domain_segment / "routes" / f"{operation_segment}.py"
            content = self.renderer.render(
                "generated_router.py.j2",
                {
                    "operation": op,
                    "bridge": bridge_contract,
                },
            )
            content = self._postprocess_python(project_dir, target, content, postprocess_mode)
            plan.changes.append(self._planned_change(target, content))

            for kind in ("request", "response", "error"):
                model = self._build_transport_model(op, kind, deprecated_operations)
                model_target = (
                    paths.generated_root
                    / domain_segment
                    / "models"
                    / f"{operation_segment}_{kind}.py"
                )
                model_content = self.renderer.render("generated_schema.py.j2", {"model": model})
                model_content = self._postprocess_python(
                    project_dir, model_target, model_content, postprocess_mode
                )
                plan.changes.append(self._planned_change(model_target, model_content))
        if effective_scaffold:
            plan.changes.extend(
                self._planned_scaffold_changes(
                    project_dir=project_dir,
                    scaffold_root=scaffold_root,
                    postprocess_mode=postprocess_mode,
                )
            )
        protected_roots = (scaffold_root,) if effective_scaffold else ()
        required_remove_paths = (
            self._scaffold_template_targets(scaffold_root) if not effective_scaffold else ()
        )
        plan.changes.extend(
            self._planned_removes(
                paths.generated_root,
                plan.changes,
                protected_roots=protected_roots,
                required_remove_paths=required_remove_paths,
            )
        )

        resolved_baseline_ref, baseline_source = self._resolve_baseline_ref(
            baseline_ref=baseline_ref,
            release_state_baseline_ref=release_state_baseline_ref,
        )
        # Compatibility comparison uses contract-only model so baseline from VCS
        # compares symmetrically across machines.
        current_normalized_model = self._build_normalized_model(ordered_operations)
        baseline_snapshot, baseline_diagnostic = self._load_baseline_snapshot(
            project_dir=project_dir,
            contracts_dir=paths.contracts_dir,
            baseline_ref=resolved_baseline_ref,
        )

        compatibility = self._build_compatibility_summary(
            current_normalized_model=current_normalized_model,
            baseline_snapshot=baseline_snapshot,
            release_number=release_number,
            grace_period_releases=config.evolution.grace_period_releases,
            deprecated_operations=deprecated_operations,
            release_state_error=release_state_error,
            baseline_ref=resolved_baseline_ref,
            baseline_source=baseline_source,
            baseline_diagnostic=baseline_diagnostic,
        )
        plan.compatibility_policy = normalized_policy
        plan.compatibility = compatibility
        plan.policy_blocked = (
            normalized_policy == "strict"
            and compatibility.overall == CompatibilityCategory.BREAKING.value
        )

        return plan

    def _build_compatibility_summary(
        self,
        current_normalized_model: dict[str, str],
        baseline_snapshot: BaselineSnapshot | None,
        release_number: int | None,
        grace_period_releases: int,
        deprecated_operations: dict[str, int],
        release_state_error: str,
        baseline_ref: str | None,
        baseline_source: str | None,
        baseline_diagnostic: str | None,
    ) -> CompatibilitySummary:
        compatibility_changes: list[CompatibilityChange] = []

        if baseline_ref and baseline_source:
            snapshot_source = baseline_snapshot.source if baseline_snapshot else "unavailable"
            compatibility_changes.append(
                CompatibilityChange(
                    code="baseline-ref-applied",
                    location="baseline",
                    detail=(
                        f"source={baseline_source},baseline_ref={baseline_ref},"
                        f"snapshot_source={snapshot_source}"
                    ),
                )
            )

        if baseline_diagnostic:
            compatibility_changes.append(
                CompatibilityChange(
                    code=baseline_diagnostic,
                    location="baseline",
                    detail=(
                        f"baseline_ref={baseline_ref}" if baseline_ref else "baseline_ref=<missing>"
                    ),
                )
            )

        if release_state_error:
            compatibility_changes.append(
                CompatibilityChange(
                    code="release-state-invalid",
                    location="release-state",
                    detail=release_state_error,
                )
            )

        # Baseline-driven classification is mandatory for breaking decisions.
        if baseline_snapshot is not None:
            baseline_normalized_model = baseline_snapshot.operations
            compatibility_changes.extend(
                self._compare_normalized_models(
                    current_normalized_model=current_normalized_model,
                    baseline_normalized_model=baseline_normalized_model,
                    release_number=release_number,
                    grace_period_releases=grace_period_releases,
                    deprecated_operations=deprecated_operations,
                )
            )

        report = classify_changes(compatibility_changes)

        return CompatibilitySummary(
            overall=report.overall.value,
            counts={
                CompatibilityCategory.NON_BREAKING.value: report.counts[
                    CompatibilityCategory.NON_BREAKING
                ],
                CompatibilityCategory.POTENTIALLY_BREAKING.value: report.counts[
                    CompatibilityCategory.POTENTIALLY_BREAKING
                ],
                CompatibilityCategory.BREAKING.value: report.counts[CompatibilityCategory.BREAKING],
            },
            diagnostics=[
                CompatibilityDiagnostic(
                    category=item.category.value,
                    code=self._normalize_compatibility_code(item.code),
                    location=item.location,
                    detail=item.detail,
                )
                for item in report.items
            ],
        )

    def _normalize_compatibility_code(self, code: str) -> str:
        candidate = str(code).strip().lower().replace("_", "-")
        if candidate.startswith("compatibility."):
            return candidate
        return f"compatibility.{candidate}"

    def _compare_normalized_models(
        self,
        current_normalized_model: dict[str, str],
        baseline_normalized_model: dict[str, str],
        release_number: int | None,
        grace_period_releases: int,
        deprecated_operations: dict[str, int],
    ) -> list[CompatibilityChange]:
        compatibility_changes: list[CompatibilityChange] = []
        current_operation_ids = set(current_normalized_model.keys())
        baseline_operation_ids = set(baseline_normalized_model.keys())

        for operation_id in sorted(current_operation_ids - baseline_operation_ids):
            compatibility_changes.append(
                CompatibilityChange(
                    code="operation-added",
                    location=f"operation:{operation_id}",
                    detail="added-vs-baseline",
                )
            )

        for operation_id in sorted(current_operation_ids & baseline_operation_ids):
            if current_normalized_model[operation_id] == baseline_normalized_model[operation_id]:
                continue
            compatibility_changes.append(
                CompatibilityChange(
                    code="response-field-type-changed",
                    location=f"operation:{operation_id}",
                    detail="fingerprint-mismatch-vs-baseline",
                )
            )

        for operation_id in sorted(baseline_operation_ids - current_operation_ids):
            deprecated_since = deprecated_operations.get(operation_id)
            if deprecated_since is None or release_number is None:
                compatibility_changes.append(
                    CompatibilityChange(
                        code="operation-removed",
                        location=f"operation:{operation_id}",
                        detail="removed-vs-baseline-without-deprecation",
                    )
                )
                continue

            releases_since_deprecation = release_number - deprecated_since
            if releases_since_deprecation < grace_period_releases:
                compatibility_changes.append(
                    CompatibilityChange(
                        code="deprecation-window-violation",
                        location=f"operation:{operation_id}",
                        detail=(
                            f"release_number={release_number},"
                            f"deprecated_since={deprecated_since},"
                            f"grace_period={grace_period_releases}"
                        ),
                    )
                )
                continue

            compatibility_changes.append(
                CompatibilityChange(
                    code="deprecation-window-satisfied",
                    location=f"operation:{operation_id}",
                    detail=(
                        f"release_number={release_number},"
                        f"deprecated_since={deprecated_since},"
                        f"grace_period={grace_period_releases}"
                    ),
                )
            )
        return compatibility_changes

    def _build_normalized_model(self, operations: list[Operation]) -> dict[str, str]:
        model = {
            operation.operation_id: self._contract_fingerprint(operation)
            for operation in operations
        }
        return {key: model[key] for key in sorted(model.keys())}

    def _load_baseline_snapshot(
        self, project_dir: Path, contracts_dir: Path, baseline_ref: str | None
    ) -> tuple[BaselineSnapshot | None, str | None]:
        if baseline_ref is None:
            return None, "baseline-missing"

        cache_snapshot = self._load_baseline_snapshot_from_cache(project_dir, baseline_ref)
        if cache_snapshot is not None:
            return cache_snapshot, None

        vcs_snapshot, vcs_error = self._load_baseline_snapshot_from_vcs(
            project_dir=project_dir,
            contracts_dir=contracts_dir,
            baseline_ref=baseline_ref,
        )
        if vcs_snapshot is None:
            return None, vcs_error
        return vcs_snapshot, None

    def _load_baseline_snapshot_from_cache(
        self, project_dir: Path, baseline_ref: str
    ) -> BaselineSnapshot | None:
        cache_file = self._baseline_cache_file(project_dir, baseline_ref)
        if not self.fs.exists(cache_file):
            return None

        try:
            if cache_file.stat().st_size > self._MAX_BASELINE_CACHE_SIZE_BYTES:
                return None
            payload = json.loads(self.fs.read_text(cache_file))
        except (OSError, ValueError, json.JSONDecodeError):
            return None

        if not isinstance(payload, dict):
            return None

        raw_operations = payload.get("operations")
        if not isinstance(raw_operations, dict):
            return None

        operations: dict[str, str] = {}
        for operation_id, fingerprint in raw_operations.items():
            op_key = str(operation_id).strip()
            op_fingerprint = str(fingerprint).strip()
            if not op_key or not op_fingerprint:
                return None
            operations[op_key] = op_fingerprint
        return BaselineSnapshot(
            baseline_ref=baseline_ref,
            operations={key: operations[key] for key in sorted(operations.keys())},
            source="cache",
        )

    def _baseline_cache_file(self, project_dir: Path, baseline_ref: str) -> Path:
        safe_ref = "".join(
            ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in baseline_ref
        )
        return project_dir / self._BASELINE_CACHE_RELATIVE_ROOT / f"{safe_ref}.json"

    def _load_baseline_snapshot_from_vcs(
        self, project_dir: Path, contracts_dir: Path, baseline_ref: str
    ) -> tuple[BaselineSnapshot | None, str]:
        try:
            contracts_rel = contracts_dir.relative_to(project_dir).as_posix()
        except ValueError:
            return None, "baseline-invalid"
        listing = self._run_git_command(
            project_dir=project_dir,
            args=("ls-tree", "-r", "--name-only", baseline_ref, "--", contracts_rel),
        )
        if listing is None:
            if not self._is_git_repository(project_dir):
                return None, "baseline-invalid"
            return None, "baseline-missing"

        baseline_operations: dict[str, str] = {}
        for entry in [
            line.strip() for line in listing.splitlines() if line.strip().endswith(".yaml")
        ]:
            content = self._run_git_command(
                project_dir=project_dir,
                args=("show", f"{baseline_ref}:{entry}"),
            )
            if content is None:
                return None, "baseline-missing"

            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError:
                return None, "baseline-invalid"
            if not isinstance(data, dict):
                return None, "baseline-invalid"

            try:
                contract_relpath = Path(entry).relative_to(Path(contracts_rel))
            except ValueError:
                return None, "baseline-invalid"
            try:
                operation = self._build_operation_from_contract_data(
                    contract_relpath=contract_relpath,
                    data=data,
                )
            except (TypeError, ValueError):
                return None, "baseline-invalid"
            baseline_operations[operation.operation_id] = self._contract_fingerprint(operation)

        return (
            BaselineSnapshot(
                baseline_ref=baseline_ref,
                operations={
                    key: baseline_operations[key] for key in sorted(baseline_operations.keys())
                },
                source="vcs",
            ),
            "",
        )

    def _build_operation_from_contract_data(
        self, contract_relpath: Path, data: dict[str, object]
    ) -> Operation:
        response_data = data.get("response", {})
        response_dict = response_data if isinstance(response_data, dict) else {}
        errors = data.get("errors", [])
        errors_list = errors if isinstance(errors, list) else []
        return Operation(
            operation_id=build_operation_id(str(contract_relpath)),
            contract=EndpointContract(
                source_path=contract_relpath,
                method=str(data.get("method", "GET")).upper(),
                path=str(data.get("path", "/")),
                auth=str(data.get("auth", "public")),
                summary=str(data.get("summary", "")),
                description=str(data.get("description", "")),
                response_status=int(response_dict.get("status", 200)),
                response_body=response_dict.get("body", {}),
                errors=errors_list,
            ),
            contract_relpath=contract_relpath,
        )

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
        return completed.stdout

    def _is_git_repository(self, project_dir: Path) -> bool:
        probe = self._run_git_command(
            project_dir=project_dir,
            args=("rev-parse", "--is-inside-work-tree"),
        )
        return probe is not None and probe.strip().lower() == "true"

    def _resolve_baseline_ref(
        self, baseline_ref: str | None, release_state_baseline_ref: str | None
    ) -> tuple[str | None, str | None]:
        if baseline_ref is not None:
            try:
                return validate_baseline_ref(baseline_ref), "cli"
            except ValueError as exc:
                raise ValueError(f"Invalid baseline_ref override: {exc}") from exc

        if release_state_baseline_ref is not None:
            try:
                return validate_baseline_ref(release_state_baseline_ref), "release-state"
            except ValueError as exc:
                raise ValueError(f"Invalid release-state baseline_ref: {exc}") from exc

        return None, None

    def _compatibility_code(self, change_type: str) -> str:
        if change_type == "ADD":
            return "operation-added"
        if change_type == "UPDATE":
            return "response-field-type-changed"
        return "auth-changed"

    def _load_existing_operation_ids(self, generated_root: Path) -> set[str]:
        operation_map_path = generated_root / "operation_map.py"
        if not self.fs.exists(operation_map_path):
            return set()

        try:
            source = self.fs.read_text(operation_map_path)
            module = ast.parse(source, filename=str(operation_map_path))
        except (OSError, ValueError, SyntaxError):
            return set()

        for node in module.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "OPERATION_MAP":
                    try:
                        operation_map = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return set()
                    if not isinstance(operation_map, dict):
                        return set()
                    return {str(key) for key in operation_map.keys()}
        return set()

    def _normalize_policy(self, policy: object) -> CompatibilityPolicy:
        candidate = policy
        for _ in range(self._MAX_HINT_RECURSION_DEPTH):
            if candidate is None:
                return "warn"
            if isinstance(candidate, str):
                break
            default = getattr(candidate, "default", None)
            if default is candidate:
                break
            if default is not None or hasattr(candidate, "default"):
                candidate = default
                continue
            break

        normalized = str(candidate).strip().lower()
        if normalized in {"warn", "strict"}:
            return cast(CompatibilityPolicy, normalized)
        raise ValueError(
            f"Unknown compatibility policy '{candidate}'. Expected one of: warn, strict."
        )

    def _planned_change(self, target: Path, content: str) -> PlannedChange:
        if not self.fs.exists(target):
            return PlannedChange(path=target, content=content, change_type="ADD")

        current = self.fs.read_text(target)
        if current != content:
            return PlannedChange(path=target, content=content, change_type="UPDATE")

        return PlannedChange(path=target, content=content, change_type="SAME")

    def _planned_scaffold_changes(
        self,
        project_dir: Path,
        scaffold_root: Path,
        postprocess_mode: PythonPostprocessMode,
    ) -> list[PlannedChange]:
        planned: list[PlannedChange] = []
        for filename, template_name in self._SCAFFOLD_TEMPLATES:
            target = scaffold_root / filename
            if self.fs.exists(target):
                # Keep manual scaffold content untouched (create-if-missing policy).
                planned.append(
                    PlannedChange(
                        path=target, content=self.fs.read_text(target), change_type="SAME"
                    )
                )
                continue

            content = self.renderer.render(template_name, {})
            content = self._postprocess_python(project_dir, target, content, postprocess_mode)
            planned.append(PlannedChange(path=target, content=content, change_type="ADD"))
        return planned

    def _resolve_scaffold_root(self, generated_root: Path, raw_scaffold_dir: str) -> Path:
        scaffold_dir = raw_scaffold_dir.strip()
        if not scaffold_dir:
            raise ValueError("Invalid generator.scaffold_dir: must be a non-empty path.")

        candidate = Path(scaffold_dir)
        if candidate.is_absolute():
            raise ValueError(
                f"Invalid generator.scaffold_dir '{raw_scaffold_dir}': "
                "absolute paths are not allowed."
            )

        generated_root_resolved = generated_root.resolve()
        scaffold_root = (generated_root_resolved / candidate).resolve(strict=False)
        try:
            scaffold_root.relative_to(generated_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Invalid generator.scaffold_dir '{raw_scaffold_dir}': "
                "path must stay inside generated root."
            ) from exc
        return scaffold_root

    def _scaffold_template_targets(self, scaffold_root: Path) -> tuple[Path, ...]:
        return tuple(scaffold_root / filename for filename, _ in self._SCAFFOLD_TEMPLATES)

    def _planned_removes(
        self,
        generated_root: Path,
        plan_changes: list[PlannedChange],
        protected_roots: tuple[Path, ...] = (),
        required_remove_paths: tuple[Path, ...] = (),
    ) -> list[PlannedChange]:
        generated_root_resolved = generated_root.resolve()
        protected_root_resolved = tuple(root.resolve(strict=False) for root in protected_roots)
        expected_paths = {change.path.resolve() for change in plan_changes}
        stale_paths_by_resolved: dict[Path, Path] = {}

        for path in self.fs.glob(generated_root, "**/*.py"):
            if not path.is_file():
                continue
            resolved_path = path.resolve()
            if self._is_protected_remove_path(resolved_path, protected_root_resolved):
                continue
            if resolved_path in expected_paths:
                continue

            existing = stale_paths_by_resolved.get(resolved_path)
            if existing is None:
                stale_paths_by_resolved[resolved_path] = path
                continue

            existing_key = self._stable_remove_sort_key(existing, generated_root_resolved)
            candidate_key = self._stable_remove_sort_key(path, generated_root_resolved)
            if candidate_key < existing_key:
                stale_paths_by_resolved[resolved_path] = path

        for path in required_remove_paths:
            if not self.fs.exists(path) or not path.is_file():
                continue
            resolved_path = path.resolve()
            if self._is_protected_remove_path(resolved_path, protected_root_resolved):
                continue
            if resolved_path in expected_paths:
                continue
            try:
                resolved_path.relative_to(generated_root_resolved)
            except ValueError:
                continue

            existing = stale_paths_by_resolved.get(resolved_path)
            if existing is None:
                stale_paths_by_resolved[resolved_path] = path
                continue

            existing_key = self._stable_remove_sort_key(existing, generated_root_resolved)
            candidate_key = self._stable_remove_sort_key(path, generated_root_resolved)
            if candidate_key < existing_key:
                stale_paths_by_resolved[resolved_path] = path

        stale_paths = sorted(
            stale_paths_by_resolved.values(),
            key=lambda stale_path: self._stable_remove_sort_key(
                stale_path, generated_root_resolved
            ),
        )
        return [
            PlannedChange(path=stale_path, content="", change_type="REMOVE")
            for stale_path in stale_paths
        ]

    def _is_protected_remove_path(
        self, resolved_path: Path, protected_roots: tuple[Path, ...]
    ) -> bool:
        for root in protected_roots:
            try:
                resolved_path.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def _stable_remove_sort_key(self, path: Path, generated_root_resolved: Path) -> tuple[str, str]:
        resolved_path = path.resolve()
        try:
            relative_path = resolved_path.relative_to(generated_root_resolved).as_posix()
        except ValueError:
            relative_path = path.as_posix()
        return (relative_path, resolved_path.as_posix())

    def _build_registry_entry(
        self,
        operation: Operation,
        deprecated_operations: dict[str, int],
        transport_segments: dict[str, tuple[str, str]],
    ) -> dict[str, object]:
        domain_segment, operation_segment = transport_segments[operation.operation_id]
        module_root = f"{domain_segment}.models.{operation_segment}"
        class_base = self._class_base(operation.operation_id)
        error_details = self._error_details(operation)
        error_schemas = self._error_schemas(operation)
        response_schema = operation.contract.response_body
        deprecation = self._deprecation_metadata(operation.operation_id, deprecated_operations)
        return {
            "operation_id": operation.operation_id,
            "method": operation.contract.method,
            "path": operation.contract.path,
            "auth": operation.contract.auth,
            "summary": operation.contract.summary,
            "description": operation.contract.description,
            "response_status": operation.contract.response_status,
            "deprecation_status": deprecation["status"],
            "deprecated_since_release": deprecation["deprecated_since_release"],
            "deprecated_since_release_literal": self._python_literal(
                deprecation["deprecated_since_release"]
            ),
            "contract_fingerprint": self._contract_fingerprint(operation),
            "response_schema_literal": self._python_literal(response_schema),
            "response_example_literal": self._python_literal(self._schema_example(response_schema)),
            "error_schemas_literal": self._python_literal(error_schemas),
            "error_examples_literal": self._python_literal(
                [item["example"] for item in error_schemas]
            ),
            "router_module": f"{domain_segment}.routes.{operation_segment}",
            "models": {
                "request": f"{module_root}_request.{class_base}Request",
                "response": f"{module_root}_response.{class_base}Response",
                "error": f"{module_root}_error.{class_base}Error",
            },
            "bridge": {
                "callable": f"{domain_segment}.routes.{operation_segment}.route",
            },
            "error_codes": [detail["code"] for detail in error_details],
        }

    def _build_bridge_contract(
        self,
        operation: Operation,
        deprecated_operations: dict[str, int],
        transport_segments: dict[str, tuple[str, str]],
    ) -> dict[str, str | int | None]:
        domain_segment, operation_segment = transport_segments[operation.operation_id]
        class_base = self._class_base(operation.operation_id)
        deprecation = self._deprecation_metadata(operation.operation_id, deprecated_operations)
        return {
            "request_module": f"{domain_segment}.models.{operation_segment}_request",
            "request_class": f"{class_base}Request",
            "response_module": f"{domain_segment}.models.{operation_segment}_response",
            "response_class": f"{class_base}Response",
            "error_module": f"{domain_segment}.models.{operation_segment}_error",
            "error_class": f"{class_base}Error",
            "contract_fingerprint": self._contract_fingerprint(operation),
            "deprecation_status": str(deprecation["status"]),
            "deprecated_since_release": cast(int | None, deprecation["deprecated_since_release"]),
            "deprecated_since_release_literal": self._python_literal(
                deprecation["deprecated_since_release"]
            ),
        }

    def _build_transport_model(
        self, operation: Operation, kind: str, deprecated_operations: dict[str, int]
    ) -> dict[str, object]:
        class_base = self._class_base(operation.operation_id)
        error_details = self._error_details(operation)
        schema_fragment = self._model_schema_fragment(operation, kind)
        deprecation = self._deprecation_metadata(operation.operation_id, deprecated_operations)
        return {
            "operation_id": operation.operation_id,
            "class_name": f"{class_base}{kind.capitalize()}",
            "kind": kind,
            "method": operation.contract.method,
            "path": operation.contract.path,
            "summary": operation.contract.summary,
            "description": operation.contract.description,
            "deprecation_status": deprecation["status"],
            "deprecated_since_release": deprecation["deprecated_since_release"],
            "deprecated_since_release_literal": self._python_literal(
                deprecation["deprecated_since_release"]
            ),
            "contract_fingerprint": self._contract_fingerprint(operation),
            "schema_fragment_literal": self._python_literal(schema_fragment),
            "schema_example_literal": self._python_literal(self._schema_example(schema_fragment)),
            "error_details": error_details,
        }

    def _transport_path_segments(self, operation: Operation) -> tuple[str, str]:
        parts = operation.contract_relpath.parts
        if len(parts) != 2:
            raise ValueError(
                "Invalid contract path layout "
                f"'{operation.contract_relpath.as_posix()}': expected single-level "
                "path '<domain>/<operation>.yaml'."
            )

        raw_domain = parts[0]
        raw_operation = Path(parts[1]).stem
        domain_segment = self._normalize_module_segment(raw_domain, "domain")
        operation_segment = self._normalize_module_segment(raw_operation, "operation")
        return domain_segment, operation_segment

    def _build_transport_segment_index(
        self, operations: list[Operation]
    ) -> dict[str, tuple[str, str]]:
        index: dict[str, tuple[str, str]] = {}
        by_target: dict[tuple[str, str], list[Operation]] = {}

        for operation in sorted(operations, key=lambda item: item.contract_relpath.as_posix()):
            segments = self._transport_path_segments(operation)
            index[operation.operation_id] = segments
            by_target.setdefault(segments, []).append(operation)

        collisions: list[str] = []
        for (domain_segment, operation_segment), bucket in sorted(by_target.items()):
            if len(bucket) < 2:
                continue
            relpaths = sorted(operation.contract_relpath.as_posix() for operation in bucket)
            collisions.append(
                "target=" f"{domain_segment}/{operation_segment},contracts={','.join(relpaths)}"
            )

        if collisions:
            raise ValueError(
                "Normalized transport path collision detected: "
                + "; ".join(collisions)
                + ". Ensure each contract maps to a unique '<domain>/<operation>.yaml' target."
            )

        return index

    def _normalize_module_segment(self, raw: str, kind: str) -> str:
        lowered = raw.strip().lower()
        replaced = re.sub(r"[^a-z0-9_]+", "_", lowered)
        collapsed = re.sub(r"_+", "_", replaced).strip("_")
        if not collapsed:
            collapsed = f"{kind}_segment"
        if collapsed[0].isdigit():
            collapsed = f"_{collapsed}"
        return collapsed

    def _deprecation_metadata(
        self, operation_id: str, deprecated_operations: dict[str, int]
    ) -> dict[str, str | int | None]:
        deprecated_since = deprecated_operations.get(operation_id)
        if deprecated_since is None:
            return {
                "status": "active",
                "deprecated_since_release": None,
            }
        return {
            "status": "deprecated",
            "deprecated_since_release": int(deprecated_since),
        }

    def _class_base(self, operation_id: str) -> str:
        parts = [part for part in re.split(r"[^a-zA-Z0-9]+", operation_id) if part]
        if not parts:
            return "Operation"
        return "".join(part[:1].upper() + part[1:] for part in parts)

    def _error_details(self, operation: Operation) -> list[dict[str, object]]:
        details = [
            {
                "code": str(error.get("code", "")).strip(),
                "http_status": int(error.get("http_status", 500)),
            }
            for error in operation.contract.errors
            if isinstance(error, dict)
        ]
        return sorted(details, key=lambda item: (item["code"], item["http_status"]))

    def _error_schemas(self, operation: Operation) -> list[dict[str, object]]:
        details = [
            {
                "code": str(error.get("code", "")).strip(),
                "http_status": int(error.get("http_status", 500)),
                "body": error.get("body", {}),
                "example": self._schema_example(error.get("body", {})),
            }
            for error in operation.contract.errors
            if isinstance(error, dict)
        ]
        return sorted(details, key=lambda item: (item["code"], item["http_status"]))

    def _schema_example(self, schema_fragment: object) -> object:
        if isinstance(schema_fragment, dict):
            return schema_fragment.get("example")
        return None

    def _contract_fingerprint(self, operation: Operation) -> str:
        response_body = operation.contract.response_body
        errors = operation.contract.errors
        payload = {
            "method": operation.contract.method,
            "path": operation.contract.path,
            "auth": operation.contract.auth,
            "summary": operation.contract.summary,
            "description": operation.contract.description,
            "response": {
                "status": operation.contract.response_status,
                "body": response_body,
                "example": self._schema_example(response_body),
            },
            "errors": errors,
            "error_examples": [
                self._schema_example(error.get("body", {}))
                for error in errors
                if isinstance(error, dict)
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _model_schema_fragment(self, operation: Operation, kind: str) -> object:
        if kind == "response":
            return operation.contract.response_body
        if kind == "error":
            return [
                {
                    "code": str(error.get("code", "")).strip(),
                    "http_status": int(error.get("http_status", 500)),
                    "body": error.get("body", {}),
                }
                for error in operation.contract.errors
                if isinstance(error, dict)
            ]
        return {}

    def _python_literal(self, value: object) -> str:
        return self._stable_python_literal(value, depth=0)

    def _stable_python_literal(self, value: object, *, depth: int = 0) -> str:
        if depth >= self._MAX_HINT_RECURSION_DEPTH:
            if isinstance(value, (dict, list, tuple)):
                return json.dumps("<truncated>", ensure_ascii=False)
        if isinstance(value, dict):
            parts = []
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
                key_literal = json.dumps(str(key), ensure_ascii=False)
                parts.append(f"{key_literal}: {self._stable_python_literal(item, depth=depth + 1)}")
            return "{" + ", ".join(parts) + "}"
        if isinstance(value, list):
            return (
                "["
                + ", ".join(self._stable_python_literal(item, depth=depth + 1) for item in value)
                + "]"
            )
        if isinstance(value, tuple):
            if not value:
                return "()"
            if len(value) == 1:
                return f"({self._stable_python_literal(value[0], depth=depth + 1)},)"
            return (
                "("
                + ", ".join(self._stable_python_literal(item, depth=depth + 1) for item in value)
                + ")"
            )
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        if value is True:
            return "True"
        if value is False:
            return "False"
        if value is None:
            return "None"
        return repr(value)

    def _postprocess_python(
        self, project_dir: Path, target: Path, content: str, mode: PythonPostprocessMode
    ) -> str:
        if target.suffix != ".py":
            return content
        return self.postprocessor.format_python_content(
            project_dir=project_dir,
            target_path=target,
            content=content,
            mode=mode,
        )

    def _generated_package_init_content(self, domain_segment: str, package_suffix: str) -> str:
        package_name = domain_segment
        if package_suffix:
            package_name = f"{domain_segment}.{package_suffix}"
        return (
            f'"""Generated package marker for {package_name}. Do not edit manually."""\n\n'
            "__all__: tuple[str, ...] = ()\n"
        )
