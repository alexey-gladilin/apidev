import asyncio
import importlib
from pathlib import Path
import sys
from typing import Any, cast

import pytest

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
    _ = service.run(tmp_path, baseline_ref="v1.0.0")
    return tmp_path / ".apidev" / "output" / "api"


def test_auth_integration_manual_wiring_passes_current_user_to_handler_request_model(
    tmp_path: Path,
) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
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
        invoke_route_with_context = cast(
            Any, getattr(router_factory_module, "invoke_route_with_context")
        )

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
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_auth_integration_generated_route_keeps_token_decode_manual(tmp_path: Path) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    route_source = (generated_dir_path / "billing" / "routes" / "get_invoice.py").read_text(
        encoding="utf-8"
    )
    assert "token" not in route_source.lower()
    assert "authorization" not in route_source.lower()
    assert "jwt" not in route_source.lower()

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
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
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_auth_integration_payload_cannot_override_trusted_current_user(tmp_path: Path) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
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
        invoke_route_with_context = cast(
            Any, getattr(router_factory_module, "invoke_route_with_context")
        )

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
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_integration_router_factory_builds_router_from_operation_map(tmp_path: Path) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any

HANDLERS: dict[str, Any] = {}


def resolve_handler(operation_id: str) -> Any:
    return HANDLERS[operation_id]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(auth_mode: str) -> Any:
    if auth_mode == "public":
        return None
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        handler_registry_module = importlib.import_module("integration.handler_registry")
        loaded_modules.append("integration.handler_registry")

        async def _manual_handler(_request: Any) -> Any:
            class _Result:
                payload = {"status": "ok"}

            return _Result()

        handlers = cast(dict[str, Any], getattr(handler_registry_module, "HANDLERS"))
        handlers["billing_get_invoice"] = _manual_handler
        build_router = cast(Any, getattr(router_factory_module, "build_router"))
        router = build_router()

        assert hasattr(router, "routes")
        route = next(
            route_obj
            for route_obj in cast(list[Any], router.routes)
            if getattr(route_obj, "path", None) == "/v1/invoices/{invoice_id}"
        )
        assert getattr(route, "operation_id", None) == "billing_get_invoice"
        methods = cast(set[str], getattr(route, "methods", set()))
        assert "GET" in methods
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_integration_router_factory_rejects_non_string_method_metadata(tmp_path: Path) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any


def resolve_handler(_operation_id: str) -> Any:
    async def _handler(_request: Any) -> Any:
        class _Result:
            payload = {}

        return _Result()
    return _handler
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(_auth_mode: str) -> Any:
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        operation_map = cast(dict[str, Any], getattr(router_factory_module, "OPERATION_MAP"))
        operation_map["billing_get_invoice"]["method"] = ["GET"]

        with pytest.raises(ValueError, match="method"):
            cast(Any, getattr(router_factory_module, "build_router"))()
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_integration_router_factory_normalizes_optional_metadata_fields(tmp_path: Path) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any


def resolve_handler(_operation_id: str) -> Any:
    async def _handler(_request: Any) -> Any:
        class _Result:
            payload = {}

        return _Result()
    return _handler
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(_auth_mode: str) -> Any:
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        operation_map = cast(dict[str, Any], getattr(router_factory_module, "OPERATION_MAP"))
        operation_map["billing_get_invoice"]["summary"] = None
        operation_map["billing_get_invoice"]["description"] = "   "

        router = cast(Any, getattr(router_factory_module, "build_router"))()
        route = next(
            route_obj
            for route_obj in cast(list[Any], router.routes)
            if getattr(route_obj, "operation_id", None) == "billing_get_invoice"
        )

        assert getattr(route, "summary", "sentinel") is None
        assert getattr(route, "description", "sentinel") is None
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


@pytest.mark.parametrize(
    ("metadata_key", "metadata_value"),
    [
        ("method", None),
        ("method", ""),
        ("method", "   "),
        ("path", None),
        ("path", ""),
        ("path", "   "),
        ("router_module", None),
        ("router_module", ""),
        ("router_module", "   "),
    ],
)
def test_integration_router_factory_rejects_null_empty_and_blank_required_metadata(
    tmp_path: Path,
    metadata_key: str,
    metadata_value: object,
) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any


def resolve_handler(_operation_id: str) -> Any:
    async def _handler(_request: Any) -> Any:
        class _Result:
            payload = {}

        return _Result()
    return _handler
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(_auth_mode: str) -> Any:
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        operation_map = cast(dict[str, Any], getattr(router_factory_module, "OPERATION_MAP"))
        operation_entry = cast(dict[str, object], operation_map["billing_get_invoice"])
        operation_entry["method"] = "GET"
        operation_entry["path"] = "/v1/invoices/{invoice_id}"
        operation_entry["router_module"] = "billing.routes.get_invoice"
        operation_entry[metadata_key] = metadata_value

        with pytest.raises(ValueError, match=metadata_key):
            cast(Any, getattr(router_factory_module, "build_router"))()
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_integration_router_factory_uses_domain_metadata_for_swagger_tag(tmp_path: Path) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any


def resolve_handler(_operation_id: str) -> Any:
    async def _handler(_request: Any) -> Any:
        class _Result:
            payload = {}

        return _Result()
    return _handler
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(_auth_mode: str) -> Any:
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        operation_map = cast(dict[str, Any], getattr(router_factory_module, "OPERATION_MAP"))
        operation_entry = cast(dict[str, object], operation_map["billing_get_invoice"])
        operation_entry["method"] = "GET"
        operation_entry["path"] = "/v1/invoices/{invoice_id}"
        operation_entry["router_module"] = "billing.routes.get_invoice"
        operation_entry["domain"] = "payments"

        router = cast(Any, getattr(router_factory_module, "build_router"))()
        route = next(
            route_obj
            for route_obj in cast(list[Any], router.routes)
            if getattr(route_obj, "operation_id", None) == "billing_get_invoice"
        )

        assert getattr(route, "tags", None) == ["payments"]
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_integration_router_factory_rejects_manual_tags_in_operation_metadata(
    tmp_path: Path,
) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any


def resolve_handler(_operation_id: str) -> Any:
    async def _handler(_request: Any) -> Any:
        class _Result:
            payload = {}

        return _Result()
    return _handler
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(_auth_mode: str) -> Any:
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        operation_map = cast(dict[str, Any], getattr(router_factory_module, "OPERATION_MAP"))
        operation_entry = cast(dict[str, object], operation_map["billing_get_invoice"])
        operation_entry["method"] = "GET"
        operation_entry["path"] = "/v1/invoices/{invoice_id}"
        operation_entry["router_module"] = "billing.routes.get_invoice"
        operation_entry["tags"] = ["manual"]

        with pytest.raises(ValueError, match="MANUAL_TAGS_FORBIDDEN"):
            cast(Any, getattr(router_factory_module, "build_router"))()
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.models", None)


def test_router_operation_map_auto_register_new_endpoint_without_router_edit(
    tmp_path: Path,
) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any

HANDLERS: dict[str, Any] = {}


def resolve_handler(operation_id: str) -> Any:
    return HANDLERS[operation_id]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(_auth_mode: str) -> Any:
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (generated_dir_path / "billing" / "routes" / "get_invoice_v2.py").write_text(
        """
from typing import Any


async def route(payload: dict[str, object], handler: Any) -> Any:
    return await handler(payload)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        handler_registry_module = importlib.import_module("integration.handler_registry")
        loaded_modules.append("integration.handler_registry")
        operation_map = cast(dict[str, Any], getattr(router_factory_module, "OPERATION_MAP"))
        operation_map["billing_get_invoice_v2"] = {
            **cast(dict[str, Any], operation_map["billing_get_invoice"]),
            "path": "/v2/invoices/{invoice_id}",
            "router_module": "billing.routes.get_invoice_v2",
            "bridge": {"callable": "billing.routes.get_invoice_v2.route"},
        }

        handlers = cast(dict[str, Any], getattr(handler_registry_module, "HANDLERS"))

        async def _handler_v1(_request: Any) -> Any:
            class _Result:
                payload = {"version": "v1"}

            return _Result()

        async def _handler_v2(_payload: dict[str, object]) -> Any:
            class _Result:
                payload = {"version": "v2"}

            return _Result()

        handlers["billing_get_invoice"] = _handler_v1
        handlers["billing_get_invoice_v2"] = _handler_v2

        router = cast(Any, getattr(router_factory_module, "build_router"))()
        registered = {
            getattr(route_obj, "operation_id", None): getattr(route_obj, "path", None)
            for route_obj in cast(list[Any], router.routes)
        }
        assert registered["billing_get_invoice"] == "/v1/invoices/{invoice_id}"
        assert registered["billing_get_invoice_v2"] == "/v2/invoices/{invoice_id}"
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.routes.get_invoice", None)
        sys.modules.pop("billing.routes.get_invoice_v2", None)
        sys.modules.pop("billing.models", None)


def test_router_operation_map_auto_register_reloads_route_callable_from_metadata(
    tmp_path: Path,
) -> None:
    generated_dir_path = _generate_bearer_contract_project(tmp_path)
    integration_root = tmp_path / "integration"
    integration_root.mkdir(parents=True, exist_ok=True)
    (integration_root / "handler_registry.py").write_text(
        """
from typing import Any

HANDLERS: dict[str, Any] = {}


def resolve_handler(operation_id: str) -> Any:
    return HANDLERS[operation_id]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (integration_root / "auth_registry.py").write_text(
        """
from typing import Any


def resolve_auth_dependency(_auth_mode: str) -> Any:
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    inserted = str(generated_dir_path)
    project_root_inserted = str(tmp_path)
    loaded_modules: list[str] = []
    sys.path.insert(0, inserted)
    sys.path.insert(1, project_root_inserted)
    try:
        router_factory_module = importlib.import_module("integration.router_factory")
        loaded_modules.append("integration.router_factory")
        handler_registry_module = importlib.import_module("integration.handler_registry")
        loaded_modules.append("integration.handler_registry")
        route_module = importlib.import_module("billing.routes.get_invoice")
        loaded_modules.append("billing.routes.get_invoice")

        async def _original_handler(_request: Any) -> Any:
            class _Result:
                payload = {"source": "original-handler"}

            return _Result()

        handlers = cast(dict[str, Any], getattr(handler_registry_module, "HANDLERS"))
        handlers["billing_get_invoice"] = _original_handler

        router = cast(Any, getattr(router_factory_module, "build_router"))()
        route = next(
            route_obj
            for route_obj in cast(list[Any], router.routes)
            if getattr(route_obj, "operation_id", None) == "billing_get_invoice"
        )
        endpoint = cast(Any, getattr(route, "endpoint"))

        async def _patched_route(payload: dict[str, object], handler: Any) -> Any:
            class _Result:
                payload = {"source": "patched-route"}

            return _Result()

        setattr(route_module, "route", _patched_route)
        response_payload = asyncio.run(endpoint(payload={"invoice_id": "inv-001"}))
        assert response_payload == {"source": "patched-route"}
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        if sys.path and sys.path[0] == project_root_inserted:
            sys.path.pop(0)
        elif len(sys.path) > 1 and sys.path[1] == project_root_inserted:
            sys.path.pop(1)
        for module_name in loaded_modules:
            sys.modules.pop(module_name, None)
        sys.modules.pop("operation_map", None)
        sys.modules.pop("integration.auth_registry", None)
        sys.modules.pop("integration.handler_registry", None)
        sys.modules.pop("integration", None)
        sys.modules.pop("billing", None)
        sys.modules.pop("billing.routes", None)
        sys.modules.pop("billing.routes.get_invoice", None)
        sys.modules.pop("billing.models", None)
