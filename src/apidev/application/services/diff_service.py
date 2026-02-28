import ast
import copy
import hashlib
import json
import stat
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
from apidev.core.rules.compatibility import CompatibilityChange, CompatibilityCategory, classify_changes
from apidev.core.rules.operation_id import build_operation_id, ensure_unique_operation_ids


class DiffService:
    _DBSPEC_HINTS_RELATIVE_PATH = Path(".dbspec") / "apidev-hints.json"
    _MAX_OPTIONAL_DBSPEC_HINTS_SIZE_BYTES = 1_000_000
    _MAX_HINT_RECURSION_DEPTH = 64
    _BASELINE_CACHE_RELATIVE_ROOT = Path(".apidev") / "cache" / "baseline"
    _MAX_BASELINE_CACHE_SIZE_BYTES = 5_000_000

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
    ) -> GenerationPlan:
        normalized_policy = self._normalize_policy(compatibility_policy)
        config = self.config_loader.load(project_dir)
        paths = resolve_paths(project_dir, config)
        postprocess_mode = config.generator.postprocess
        existing_operation_ids = self._load_existing_operation_ids(paths.generated_root)

        operations = self.loader.load(paths.contracts_dir)
        errors = ensure_unique_operation_ids(operations)
        if errors:
            raise ValueError("; ".join(errors))
        ordered_operations = sorted(operations, key=lambda op: op.operation_id)
        enriched_operations = self._merge_optional_dbspec_hints(project_dir, ordered_operations)

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
            self._build_registry_entry(op, deprecated_operations)
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

        for op in enriched_operations:
            bridge_contract = self._build_bridge_contract(op, deprecated_operations)
            target = paths.generated_root / "routers" / f"{op.operation_id}.py"
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
                    paths.generated_root / "transport" / "models" / f"{op.operation_id}_{kind}.py"
                )
                model_content = self.renderer.render("generated_schema.py.j2", {"model": model})
                model_content = self._postprocess_python(
                    project_dir, model_target, model_content, postprocess_mode
                )
                plan.changes.append(self._planned_change(model_target, model_content))

        resolved_baseline_ref, baseline_source = self._resolve_baseline_ref(
            baseline_ref=baseline_ref,
            release_state_baseline_ref=release_state_baseline_ref,
        )
        # Compatibility comparison uses contract-only model (no dbspec hints) so baseline
        # from VCS (contract-only) compares symmetrically; generation uses enriched_operations.
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

    def _merge_optional_dbspec_hints(
        self, project_dir: Path, operations: list[Operation]
    ) -> list[Operation]:
        hints_payload = self._load_optional_dbspec_hints(project_dir)
        operation_hints = self._as_dict(hints_payload.get("operations"))
        if not operation_hints:
            return operations

        merged_operations: list[Operation] = []
        for operation in operations:
            raw_hints = self._as_dict(operation_hints.get(operation.operation_id))
            if not raw_hints:
                merged_operations.append(operation)
                continue

            merged_response_body = self._merge_with_contract_priority(
                operation.contract.response_body,
                raw_hints.get("response_body"),
                depth=0,
            )
            merged_errors = self._merge_error_hints(operation.contract.errors, raw_hints.get("errors"))
            merged_operations.append(
                Operation(
                    operation_id=operation.operation_id,
                    contract=EndpointContract(
                        source_path=operation.contract.source_path,
                        method=operation.contract.method,
                        path=operation.contract.path,
                        auth=operation.contract.auth,
                        summary=operation.contract.summary,
                        description=operation.contract.description,
                        response_status=operation.contract.response_status,
                        response_body=self._as_dict(merged_response_body),
                        errors=merged_errors,
                    ),
                    contract_relpath=operation.contract_relpath,
                )
            )
        return merged_operations

    def _load_optional_dbspec_hints(self, project_dir: Path) -> dict[str, object]:
        hints_path = project_dir / self._DBSPEC_HINTS_RELATIVE_PATH
        if not self.fs.exists(hints_path):
            return {}

        try:
            if not self._is_trusted_optional_hints_path(project_dir, hints_path):
                return {}
            if hints_path.stat().st_size > self._MAX_OPTIONAL_DBSPEC_HINTS_SIZE_BYTES:
                return {}
            data = json.loads(self.fs.read_text(hints_path))
        except (OSError, ValueError, json.JSONDecodeError):
            return {}
        return self._as_dict(data)

    def _is_trusted_optional_hints_path(self, project_dir: Path, hints_path: Path) -> bool:
        try:
            project_root = project_dir.resolve(strict=False)
            hints_lstat = hints_path.lstat()
            if not stat.S_ISREG(hints_lstat.st_mode):
                return False

            resolved_hints_path = hints_path.resolve(strict=True)
            if not resolved_hints_path.is_relative_to(project_root):
                return False

            resolved_stat = resolved_hints_path.stat()
            return stat.S_ISREG(resolved_stat.st_mode)
        except OSError:
            return False

    def _merge_error_hints(
        self, errors: list[dict[str, object]], error_hints: object
    ) -> list[dict[str, object]]:
        indexed_hints = self._build_error_hints_index(error_hints)
        if not indexed_hints:
            return copy.deepcopy(errors)

        merged: list[dict[str, object]] = []
        for error in errors:
            if not isinstance(error, dict):
                continue

            code = str(error.get("code", "")).strip()
            http_status = self._coerce_http_status(error.get("http_status"), default=500)
            hint_body = indexed_hints.get(self._error_hint_key(code, http_status))

            current = copy.deepcopy(error)
            if hint_body is not None:
                current["body"] = self._merge_with_contract_priority(
                    current.get("body", {}), hint_body, depth=0
                )
            merged.append(current)
        return merged

    def _build_error_hints_index(self, error_hints: object) -> dict[str, object]:
        if isinstance(error_hints, dict):
            return {str(key): value for key, value in error_hints.items()}
        if isinstance(error_hints, list):
            indexed: dict[str, object] = {}
            for item in error_hints:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("code", "")).strip()
                http_status = self._coerce_http_status(item.get("http_status"), default=500)
                indexed[self._error_hint_key(code, http_status)] = item.get("body")
            return indexed
        return {}

    def _error_hint_key(self, code: str, http_status: int) -> str:
        return f"{code}:{http_status}"

    def _as_dict(self, value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return {}

    def _coerce_http_status(self, value: object, default: int) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default

    def _merge_with_contract_priority(
        self, contract_value: object, hint_value: object, *, depth: int = 0
    ) -> object:
        if depth >= self._MAX_HINT_RECURSION_DEPTH:
            return copy.deepcopy(contract_value) if contract_value is not None else {}

        if isinstance(contract_value, dict):
            hint_dict = self._as_dict(hint_value)
            merged: dict[str, object] = {}
            keys = sorted(set(contract_value.keys()) | set(hint_dict.keys()), key=str)
            next_depth = depth + 1
            for key in keys:
                if key in contract_value and key in hint_dict:
                    merged[key] = self._merge_with_contract_priority(
                        contract_value[key], hint_dict[key], depth=next_depth
                    )
                elif key in contract_value:
                    merged[key] = copy.deepcopy(contract_value[key])
                else:
                    merged[key] = self._canonicalize_hint_value(hint_dict[key], depth=next_depth)
            return merged

        if isinstance(contract_value, list):
            # Contract list order/shape is the source of truth.
            return copy.deepcopy(contract_value)

        # Scalar conflict: contract value always wins.
        return copy.deepcopy(contract_value)

    def _canonicalize_hint_value(self, hint_value: object, *, depth: int = 0) -> object:
        if depth >= self._MAX_HINT_RECURSION_DEPTH:
            return self._truncate_at_depth_limit(hint_value)

        if isinstance(hint_value, dict):
            return {
                key: self._canonicalize_hint_value(value, depth=depth + 1)
                for key, value in sorted(hint_value.items(), key=lambda item: str(item[0]))
            }
        if isinstance(hint_value, list):
            canonical_items = [
                self._canonicalize_hint_value(item, depth=depth + 1) for item in hint_value
            ]
            return sorted(
                canonical_items,
                key=lambda item: json.dumps(
                    item,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            )
        return copy.deepcopy(hint_value)

    def _truncate_at_depth_limit(self, value: object) -> object:
        """Return a safe copy with nested dict/list replaced by placeholder to avoid deep recursion."""
        if isinstance(value, dict):
            return {
                k: ("<truncated>" if isinstance(v, (dict, list)) else copy.deepcopy(v))
                for k, v in sorted(value.items(), key=lambda item: str(item[0]))
            }
        if isinstance(value, list):
            truncated = [
                "<truncated>" if isinstance(item, (dict, list)) else copy.deepcopy(item)
                for item in value
            ]
            return sorted(
                truncated,
                key=lambda item: json.dumps(
                    item,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            )
        return copy.deepcopy(value)

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
                        f"baseline_ref={baseline_ref}"
                        if baseline_ref
                        else "baseline_ref=<missing>"
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
                CompatibilityCategory.BREAKING.value: report.counts[
                    CompatibilityCategory.BREAKING
                ],
            },
            diagnostics=[
                CompatibilityDiagnostic(
                    category=item.category.value,
                    code=item.code,
                    location=item.location,
                    detail=item.detail,
                )
                for item in report.items
            ],
        )

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
        safe_ref = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in baseline_ref)
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
            return None, "baseline-missing"

        baseline_operations: dict[str, str] = {}
        for entry in [line.strip() for line in listing.splitlines() if line.strip().endswith(".yaml")]:
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
                operations={key: baseline_operations[key] for key in sorted(baseline_operations.keys())},
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
        completed = subprocess.run(
            ["git", *args],
            cwd=project_dir,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            return None
        return completed.stdout

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

    def _normalize_policy(self, policy: str) -> CompatibilityPolicy:
        normalized = str(policy).strip().lower()
        if normalized in {"warn", "strict"}:
            return cast(CompatibilityPolicy, normalized)
        raise ValueError(
            f"Unknown compatibility policy '{policy}'. Expected one of: warn, strict."
        )

    def _planned_change(self, target: Path, content: str) -> PlannedChange:
        if not self.fs.exists(target):
            return PlannedChange(path=target, content=content, change_type="ADD")

        current = self.fs.read_text(target)
        if current != content:
            return PlannedChange(path=target, content=content, change_type="UPDATE")

        return PlannedChange(path=target, content=content, change_type="SAME")

    def _build_registry_entry(
        self, operation: Operation, deprecated_operations: dict[str, int]
    ) -> dict[str, object]:
        class_base = self._class_base(operation.operation_id)
        error_details = self._error_details(operation)
        error_schemas = self._error_schemas(operation)
        response_schema = operation.contract.response_body
        deprecation = self._deprecation_metadata(operation.operation_id, deprecated_operations)
        return {
            "operation_id": operation.operation_id,
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
            "response_schema_literal": self._python_literal(response_schema),
            "response_example_literal": self._python_literal(self._schema_example(response_schema)),
            "error_schemas_literal": self._python_literal(error_schemas),
            "error_examples_literal": self._python_literal(
                [item["example"] for item in error_schemas]
            ),
            "router_module": f"routers.{operation.operation_id}",
            "models": {
                "request": (
                    f"transport.models.{operation.operation_id}_request.{class_base}Request"
                ),
                "response": (
                    f"transport.models.{operation.operation_id}_response.{class_base}Response"
                ),
                "error": f"transport.models.{operation.operation_id}_error.{class_base}Error",
            },
            "bridge": {
                "callable": f"routers.{operation.operation_id}.route",
            },
            "error_codes": [detail["code"] for detail in error_details],
        }

    def _build_bridge_contract(
        self, operation: Operation, deprecated_operations: dict[str, int]
    ) -> dict[str, str | int | None]:
        class_base = self._class_base(operation.operation_id)
        deprecation = self._deprecation_metadata(operation.operation_id, deprecated_operations)
        return {
            "request_module": f"transport.models.{operation.operation_id}_request",
            "request_class": f"{class_base}Request",
            "response_module": f"transport.models.{operation.operation_id}_response",
            "response_class": f"{class_base}Response",
            "error_module": f"transport.models.{operation.operation_id}_error",
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
        return "".join(part.capitalize() for part in operation_id.split("_"))

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
            return "[" + ", ".join(self._stable_python_literal(item, depth=depth + 1) for item in value) + "]"
        if isinstance(value, tuple):
            if not value:
                return "()"
            if len(value) == 1:
                return f"({self._stable_python_literal(value[0], depth=depth + 1)},)"
            return "(" + ", ".join(self._stable_python_literal(item, depth=depth + 1) for item in value) + ")"
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
