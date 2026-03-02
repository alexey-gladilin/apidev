import asyncio
import importlib
from pathlib import Path
import sys
from typing import Any, cast

from apidev.application.services.generate_service import GenerateService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem
from apidev.infrastructure.output.python_postprocessor import PythonPostprocessor
from apidev.infrastructure.output.writer import SafeWriter
from apidev.infrastructure.templates.jinja_renderer import JinjaTemplateRenderer


def _generate_bearer_contract_project(tmp_path: Path) -> Path:
    (tmp_path / ".apidev" / "contracts" / "billing").mkdir(parents=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / ".apidev" / "contracts" / "billing" / "get_invoice.yaml").write_text(
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Get invoice details
response:
  status: 200
  body:
    type: object
errors: []
""".strip(),
        encoding="utf-8",
    )

    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=YamlContractLoader(),
        renderer=JinjaTemplateRenderer(custom_templates_dir=tmp_path / ".apidev" / "templates"),
        fs=fs,
        writer=SafeWriter(fs=fs),
        postprocessor=PythonPostprocessor(),
    )
    _ = service.run(tmp_path)
    return tmp_path / ".apidev" / "output" / "api"


def test_auth_integration_manual_wiring_passes_current_user_to_handler_request_model(
    tmp_path: Path,
) -> None:
    generated_root = _generate_bearer_contract_project(tmp_path)
    inserted = str(generated_root)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    try:
        operation_map_module = importlib.import_module("operation_map")
        loaded_modules.append("operation_map")
        operation_map = cast(dict[str, Any], operation_map_module.OPERATION_MAP)
        entry = cast(dict[str, Any], operation_map["billing_get_invoice"])

        route_callable_path = str(cast(dict[str, Any], entry["bridge"])["callable"])
        route_module_name, route_callable_name = route_callable_path.rsplit(".", 1)
        route_module = importlib.import_module(route_module_name)
        loaded_modules.append(route_module_name)
        route_callable = cast(Any, getattr(route_module, route_callable_name))

        response_class_path = str(cast(dict[str, Any], entry["models"])["response"])
        response_module_name, response_class_name = response_class_path.rsplit(".", 1)
        response_module = importlib.import_module(response_module_name)
        loaded_modules.append(response_module_name)
        response_class = cast(Any, getattr(response_module, response_class_name))

        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        invoke_route_with_context = cast(Any, getattr(router_factory_module, "invoke_route_with_context"))

        captured_payload: dict[str, object] = {}

        async def _manual_handler(request: Any) -> Any:
            captured_payload.update(cast(dict[str, object], request.payload or {}))
            return response_class(payload={"status": "ok"})

        payload = {"invoice_id": "inv-001"}
        current_user = {"id": "user-42", "scope": "billing:read"}
        _ = asyncio.run(
            invoke_route_with_context(
                route_callable=route_callable,
                handler=_manual_handler,
                payload=payload,
                current_user=current_user,
            )
        )

        assert captured_payload["invoice_id"] == "inv-001"
        assert captured_payload["current_user"] == current_user
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_auth_integration_generated_route_keeps_token_decode_manual(tmp_path: Path) -> None:
    generated_root = _generate_bearer_contract_project(tmp_path)
    route_source = (generated_root / "billing" / "routes" / "get_invoice.py").read_text(encoding="utf-8")
    assert "token" not in route_source.lower()
    assert "authorization" not in route_source.lower()
    assert "jwt" not in route_source.lower()

    inserted = str(generated_root)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    try:
        operation_map_module = importlib.import_module("operation_map")
        loaded_modules.append("operation_map")
        operation_map = cast(dict[str, Any], operation_map_module.OPERATION_MAP)
        entry = cast(dict[str, Any], operation_map["billing_get_invoice"])

        route_callable_path = str(cast(dict[str, Any], entry["bridge"])["callable"])
        route_module_name, route_callable_name = route_callable_path.rsplit(".", 1)
        route_module = importlib.import_module(route_module_name)
        loaded_modules.append(route_module_name)
        route_callable = cast(Any, getattr(route_module, route_callable_name))

        response_class_path = str(cast(dict[str, Any], entry["models"])["response"])
        response_module_name, response_class_name = response_class_path.rsplit(".", 1)
        response_module = importlib.import_module(response_module_name)
        loaded_modules.append(response_module_name)
        response_class = cast(Any, getattr(response_module, response_class_name))

        captured_payload: dict[str, object] = {}

        async def _manual_handler(request: Any) -> Any:
            captured_payload.update(cast(dict[str, object], request.payload or {}))
            return response_class(payload={"status": "ok"})

        _ = asyncio.run(route_callable(payload={"invoice_id": "inv-001"}, handler=_manual_handler))
        assert captured_payload == {"invoice_id": "inv-001"}
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_auth_integration_payload_cannot_override_trusted_current_user(tmp_path: Path) -> None:
    generated_root = _generate_bearer_contract_project(tmp_path)
    inserted = str(generated_root)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    try:
        operation_map_module = importlib.import_module("operation_map")
        loaded_modules.append("operation_map")
        operation_map = cast(dict[str, Any], operation_map_module.OPERATION_MAP)
        entry = cast(dict[str, Any], operation_map["billing_get_invoice"])

        route_callable_path = str(cast(dict[str, Any], entry["bridge"])["callable"])
        route_module_name, route_callable_name = route_callable_path.rsplit(".", 1)
        route_module = importlib.import_module(route_module_name)
        loaded_modules.append(route_module_name)
        route_callable = cast(Any, getattr(route_module, route_callable_name))

        response_class_path = str(cast(dict[str, Any], entry["models"])["response"])
        response_module_name, response_class_name = response_class_path.rsplit(".", 1)
        response_module = importlib.import_module(response_module_name)
        loaded_modules.append(response_module_name)
        response_class = cast(Any, getattr(response_module, response_class_name))

        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        invoke_route_with_context = cast(Any, getattr(router_factory_module, "invoke_route_with_context"))

        captured_payload: dict[str, object] = {}

        async def _manual_handler(request: Any) -> Any:
            captured_payload.update(cast(dict[str, object], request.payload or {}))
            return response_class(payload={"status": "ok"})

        untrusted_payload = {
            "invoice_id": "inv-001",
            "current_user": {"id": "attacker"},
        }
        trusted_user = {"id": "user-42"}
        _ = asyncio.run(
            invoke_route_with_context(
                route_callable=route_callable,
                handler=_manual_handler,
                payload=untrusted_payload,
                current_user=trusted_user,
            )
        )

        assert captured_payload["current_user"] == trusted_user
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)
