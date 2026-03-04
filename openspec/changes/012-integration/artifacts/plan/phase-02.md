# Phase 02: Runtime adapter и OpenAPI extensions

## Цель фазы
Собрать единый runtime/OpenAPI projection слой на основе operation metadata.

## Scope
- Реализовать runtime adapter, строящий маршруты через `APIRouter.add_api_route(...)`.
- Пробросить metadata: method/path/auth/errors/deprecated/summary/description.
- Вычислять Swagger tags автоматически из домена операции и валидировать наличие manual `tags` как fail-fast.
- Добавить `openapi.include_extensions` toggle для `x-apidev-*`.
- Обеспечить соответствие runtime wiring референсному коду из `artifacts/design/05-integration-reference.md`.

## Выходы
- Актуализированные templates runtime adapter и OpenAPI projection.
- Integration/snapshot тесты на согласованность runtime и OpenAPI output.
- Подтвержденное соответствие reference integration contract (auto-register, handler+mapping only).

## Verification Gate
- `uv run pytest tests/integration -k "router or openapi or extensions"`
- `uv run pytest tests/unit -k "operation_map or metadata"`
- `uv run pytest tests/integration -k "auto_register or operation_map"`
- `uv run ruff check src tests`
- `uv run mypy src`

## Риски
- Расхождение между runtime route registration и generated OpenAPI.
- Потеря совместимости существующих integration templates.

## Definition of Done
- Runtime/OpenAPI projection стабилен и детерминирован.
- Toggle extensions управляет только `x-apidev-*` полями.
- Runtime wiring соответствует reference integration contract из design artifacts.
- Проверки фазы проходят полностью.
