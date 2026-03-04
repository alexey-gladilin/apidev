# Интеграционный код-контракт: Runtime Adapter Reference

## Назначение
Этот документ фиксирует референсную форму integration-кода, которую implement-фаза обязана воспроизвести по поведению.
Код ниже не является production-реализацией в рамках proposal-фазы, а задает обязательный shape runtime wiring.

## Reference Snippet (целевое поведение)
```python
from fastapi import APIRouter, Depends
from generated.operation_map import OPERATION_MAP
from integration.handler_registry import resolve_handler
from integration.auth_registry import resolve_auth_dependency


def build_router() -> APIRouter:
    router = APIRouter()
    for operation_id in sorted(OPERATION_MAP):
        meta = dict(OPERATION_MAP[operation_id])
        handler = resolve_handler(operation_id)
        auth_dep = resolve_auth_dependency(meta.get("auth", "public"))
        deps = [Depends(auth_dep)] if auth_dep else []

        async def endpoint(payload=None, current_user=None, *, _meta=meta, _handler=handler):
            route = _load_generated_route(_meta["router_module"])
            result = await invoke_route_with_context(
                route_callable=route,
                handler=_handler,
                payload=payload,
                current_user=current_user,
            )
            return getattr(result, "payload", None) or {}

        router.add_api_route(
            meta["path"],
            endpoint,
            methods=[meta["method"]],
            operation_id=operation_id,
            summary=meta.get("summary"),
            description=meta.get("description"),
            deprecated=meta.get("deprecation_status") == "deprecated",
            responses=_build_responses(meta),
            tags=[_resolve_domain_tag(meta, operation_id)],
            dependencies=deps,
        )
    return router
```

## Обязательные свойства реализации
- Runtime adapter должен регистрировать endpoint-ы через `APIRouter.add_api_route(...)` на основе `OPERATION_MAP`.
- Новые endpoint-ы должны подключаться автоматически из `operation_map` без ручного добавления route-definition.
- Для нового endpoint вручную добавляются только handler и mapping в integration-layer.
- Route callable должен резолвиться по `router_module` внутри endpoint-вызова (lazy resolve), чтобы wiring всегда соответствовал актуальному `operation_map`.
- В `add_api_route` обязателен проброс:
  - `operation_id`, `summary`, `description`, `deprecated`;
  - `responses` (success + declared errors);
  - `tags` (доменная группировка, вычисляемая из domain layout операции);
  - auth dependency на основе `auth` режима.

## Правило доменной группировки
- Source of truth для домена — domain layout операции (структура operation map / domain namespace).
- `tags` не являются первичным пользовательским полем для выбора домена.
- При наличии manual `tags` в metadata операции генерация должна завершаться fail-fast validation error.

## Acceptance Hooks
- Integration tests должны проверять появление нового endpoint при обновлении `operation_map` без ручного редактирования router-кода.
- OpenAPI snapshot должен содержать error responses/examples/tags, соответствующие `operation_map` и contract metadata.
- Regression tests должны подтверждать, что runtime routing и OpenAPI projection не расходятся.
