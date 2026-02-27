from pathlib import Path
import hashlib
import json
from pprint import pformat
from apidev.application.dto.resolved_paths import resolve_paths
from apidev.application.dto.generation_plan import GenerationPlan, PlannedChange
from apidev.core.models.operation import Operation
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.core.rules.operation_id import ensure_unique_operation_ids
from apidev.infrastructure.output.postprocess import PostprocessMode, format_python_content


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
        postprocess_mode = config.generator.postprocess

        operations = self.loader.load(paths.contracts_dir)
        errors = ensure_unique_operation_ids(operations)
        if errors:
            raise ValueError("; ".join(errors))
        ordered_operations = sorted(operations, key=lambda op: op.operation_id)

        plan = GenerationPlan(generated_root=paths.generated_root)

        registry_entries = [self._build_registry_entry(op) for op in ordered_operations]
        operation_map_target = paths.generated_root / "operation_map.py"
        operation_map_content = self.renderer.render(
            "generated_operation_map.py.j2",
            {
                "operations": ordered_operations,
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

        for op in ordered_operations:
            bridge_contract = self._build_bridge_contract(op)
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
                model = self._build_transport_model(op, kind)
                model_target = (
                    paths.generated_root / "transport" / "models" / f"{op.operation_id}_{kind}.py"
                )
                model_content = self.renderer.render("generated_schema.py.j2", {"model": model})
                model_content = self._postprocess_python(
                    project_dir, model_target, model_content, postprocess_mode
                )
                plan.changes.append(self._planned_change(model_target, model_content))

        return plan

    def _planned_change(self, target: Path, content: str) -> PlannedChange:
        if not self.fs.exists(target):
            return PlannedChange(path=target, content=content, change_type="ADD")

        current = self.fs.read_text(target)
        if current != content:
            return PlannedChange(path=target, content=content, change_type="UPDATE")

        return PlannedChange(path=target, content=content, change_type="SAME")

    def _build_registry_entry(self, operation: Operation) -> dict[str, object]:
        class_base = self._class_base(operation.operation_id)
        error_details = self._error_details(operation)
        return {
            "operation_id": operation.operation_id,
            "method": operation.contract.method,
            "path": operation.contract.path,
            "summary": operation.contract.summary,
            "description": operation.contract.description,
            "contract_fingerprint": self._contract_fingerprint(operation),
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

    def _build_bridge_contract(self, operation: Operation) -> dict[str, str]:
        class_base = self._class_base(operation.operation_id)
        return {
            "request_module": f"transport.models.{operation.operation_id}_request",
            "request_class": f"{class_base}Request",
            "response_module": f"transport.models.{operation.operation_id}_response",
            "response_class": f"{class_base}Response",
            "error_module": f"transport.models.{operation.operation_id}_error",
            "error_class": f"{class_base}Error",
            "contract_fingerprint": self._contract_fingerprint(operation),
        }

    def _build_transport_model(self, operation: Operation, kind: str) -> dict[str, object]:
        class_base = self._class_base(operation.operation_id)
        error_details = self._error_details(operation)
        schema_fragment = self._model_schema_fragment(operation, kind)
        return {
            "operation_id": operation.operation_id,
            "class_name": f"{class_base}{kind.capitalize()}",
            "kind": kind,
            "method": operation.contract.method,
            "path": operation.contract.path,
            "summary": operation.contract.summary,
            "description": operation.contract.description,
            "contract_fingerprint": self._contract_fingerprint(operation),
            "schema_fragment_literal": self._python_literal(schema_fragment),
            "error_details": error_details,
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

    def _contract_fingerprint(self, operation: Operation) -> str:
        payload = {
            "method": operation.contract.method,
            "path": operation.contract.path,
            "auth": operation.contract.auth,
            "summary": operation.contract.summary,
            "description": operation.contract.description,
            "response": {
                "status": operation.contract.response_status,
                "body": operation.contract.response_body,
            },
            "errors": operation.contract.errors,
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
        return pformat(value, sort_dicts=True, width=100)

    def _postprocess_python(
        self, project_dir: Path, target: Path, content: str, mode: PostprocessMode
    ) -> str:
        if target.suffix != ".py":
            return content
        return format_python_content(
            project_dir=project_dir,
            target_path=target,
            content=content,
            mode=mode,
        )
