from pathlib import Path
from dataclasses import dataclass
from importlib import resources
from typing import Literal
import tomllib

from apidev.application.dto.resolved_paths import ResolvedPaths, resolve_paths
from apidev.core.models.config import ApidevConfig
from apidev.core.ports.filesystem import FileSystemPort

DEFAULT_CONTRACT = """method: GET
path: /v1/health
auth: public
description: Returns health status.
response:
  status: 200
  body:
    type: object
    properties:
      status:
        type: string
        required: true
errors:
  - code: INTERNAL_ERROR
    http_status: 500
    body:
      type: object
      properties:
        error_code:
          type: string
          required: true
        message:
          type: string
          required: true
"""


class InitService:
    _SCAFFOLD_TEMPLATES_RUNTIME_NONE: tuple[str, ...] = (
        "integration_handler_registry.py.j2",
        "integration_error_mapper.py.j2",
    )
    _SCAFFOLD_TEMPLATES_FASTAPI: tuple[str, ...] = (
        "integration_handler_registry.py.j2",
        "integration_router_factory.py.j2",
        "integration_auth_registry.py.j2",
        "integration_error_mapper.py.j2",
    )
    _GENERATED_INTEGRATION_TEMPLATES: tuple[str, ...] = (
        "generated_operation_map.py.j2",
        "generated_openapi_docs.py.j2",
        "generated_router.py.j2",
        "generated_schema.py.j2",
    )

    def __init__(self, fs: FileSystemPort, default_config_text: str):
        self.fs = fs
        self.default_config_text = default_config_text

    def run(
        self,
        project_dir: Path,
        mode: Literal["create", "repair", "force"] = "create",
        runtime: Literal["fastapi", "none"] = "fastapi",
        integration_mode: Literal["off", "scaffold", "full"] = "scaffold",
    ) -> "InitResult":
        project_root = project_dir.resolve(strict=False)
        config_path = project_root / ".apidev" / "config.toml"
        existing_config = self._load_existing_config(config_path)

        paths = resolve_paths(project_root, existing_config or ApidevConfig())

        self._validate_init_managed_paths(project_root=project_root, paths=paths)

        changed = 0
        invalid_paths: list[Path] = []

        for directory in (paths.apidev_dir, paths.contracts_dir, paths.templates_dir):
            if not self.fs.exists(directory):
                self.fs.mkdir(directory, parents=True)
                changed += 1

        sample_contract = paths.contracts_dir / "system" / "health.yaml"
        managed_templates = self._load_managed_templates(
            runtime=runtime,
            integration_mode=integration_mode,
        )

        managed_defaults = {
            paths.config_path: self.default_config_text,
            sample_contract: DEFAULT_CONTRACT,
        }
        for template_name, template_content in managed_templates.items():
            managed_defaults[paths.templates_dir / template_name] = template_content

        for file_path, default_content in managed_defaults.items():
            if self.fs.exists(file_path):
                if file_path == paths.config_path:
                    if self._load_existing_config(file_path) is None:
                        invalid_paths.append(file_path)
                    continue

                current = self.fs.read_text(file_path)
                if current != default_content:
                    invalid_paths.append(file_path)
            else:
                self.fs.mkdir(file_path.parent, parents=True)
                self.fs.write_text(file_path, default_content)
                changed += 1

        if mode == "create":
            if invalid_paths:
                raise InitRepairRequiredError(invalid_paths=invalid_paths)
            status: Literal["already_initialized", "initialized"] = (
                "already_initialized" if changed == 0 else "initialized"
            )
            return InitResult(status=status, changed=changed)

        if mode == "repair":
            for file_path in invalid_paths:
                self.fs.write_text(file_path, managed_defaults[file_path])
                changed += 1
            return InitResult(status="repaired", changed=changed)

        for file_path, default_content in managed_defaults.items():
            self.fs.write_text(file_path, default_content)
        return InitResult(status="forced", changed=changed + len(managed_defaults))

    def _load_existing_config(self, config_path: Path) -> ApidevConfig | None:
        if not self.fs.exists(config_path):
            return None

        try:
            raw = self.fs.read_text(config_path)
            data = tomllib.loads(raw)
            return ApidevConfig.model_validate(data)
        except (tomllib.TOMLDecodeError, ValueError):
            return None

    def _validate_init_managed_paths(self, *, project_root: Path, paths: ResolvedPaths) -> None:
        managed_paths = (
            paths.apidev_dir,
            paths.config_path,
            paths.contracts_dir,
            paths.templates_dir,
        )
        for managed_path in managed_paths:
            self._ensure_path_in_project(project_root=project_root, candidate=managed_path)

    def _ensure_path_in_project(self, *, project_root: Path, candidate: Path) -> None:
        resolved_candidate = candidate.resolve(strict=False)
        try:
            resolved_candidate.relative_to(project_root)
        except ValueError as exc:
            raise InitPathBoundaryError(
                path=resolved_candidate,
                project_root=project_root,
            ) from exc

    def _load_managed_templates(
        self,
        *,
        runtime: Literal["fastapi", "none"],
        integration_mode: Literal["off", "scaffold", "full"],
    ) -> dict[str, str]:
        if integration_mode == "off":
            template_files: tuple[str, ...] = ()
        elif integration_mode == "scaffold":
            if runtime == "none":
                template_files = self._SCAFFOLD_TEMPLATES_RUNTIME_NONE
            else:
                template_files = self._SCAFFOLD_TEMPLATES_FASTAPI
        else:
            if runtime == "none":
                raise ValueError(
                    "config.INIT_MODE_CONFLICT: --integration-mode full requires --runtime fastapi."
                )
            template_files = (
                self._SCAFFOLD_TEMPLATES_FASTAPI + self._GENERATED_INTEGRATION_TEMPLATES
            )

        templates_root = resources.files("apidev").joinpath("templates")
        managed: dict[str, str] = {}
        for template_name in template_files:
            managed[template_name] = templates_root.joinpath(template_name).read_text(
                encoding="utf-8"
            )
        return managed


@dataclass(slots=True)
class InitResult:
    status: Literal["initialized", "already_initialized", "repaired", "forced"]
    changed: int


class InitRepairRequiredError(ValueError):
    def __init__(self, invalid_paths: list[Path]):
        super().__init__("Project has invalid init-managed file(s).")
        self.invalid_paths = invalid_paths


class InitPathBoundaryError(ValueError):
    def __init__(self, path: Path, project_root: Path):
        super().__init__(
            "validation.PATH_BOUNDARY_VIOLATION: "
            f"init-managed path must stay inside project_dir ({project_root}): {path}"
        )
        self.path = path
        self.project_root = project_root
