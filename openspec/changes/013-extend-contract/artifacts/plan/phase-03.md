# Phase 03: Тестирование, документация и readiness

## Цель фазы
Закрыть change регрессионным покрытием, синхронизацией документации и strict readiness-проверкой.

## Scope
- Добавить unit/integration/contract тесты по request-модели и OpenAPI проекции.
- Зафиксировать отсутствие регрессий для `response/errors` и legacy-контрактов без `request` (если допускается change-правилами).
- Обновить документацию contract/CLI формата.
- Подтвердить готовность change строгой OpenSpec-валидацией и plan handoff.

## Выходы
- Regression suite для новых request-сценариев.
- Актуальные `docs/reference/contract-format.md` и `docs/reference/cli-contract.md`.
- Подтвержденная implement-readiness change-пакета.

## Verification Gate
- `uv run pytest tests/unit tests/integration tests/contract -k "request or openapi or operation_map"`
- `uv run pytest tests/integration -k "legacy or backwards"`
- `uv run ruff check src tests`
- `uv run mypy src`
- `openspec validate 013-extend-contract --strict --no-interactive`

## Риски
- Дрейф документации относительно фактической генерации.
- Неполное покрытие edge-кейсов path/query/body сочетаний.

## Definition of Done
- Тесты фиксируют happy-path и fail-fast сценарии request-контракта.
- Документация отражает точный контракт `request.path/query/body` и примеры.
- Регрессии по `response/errors` отсутствуют.
- Strict OpenSpec validation проходит без ошибок.
