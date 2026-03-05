# Phase 02: Генерация request metadata и OpenAPI

## Цель фазы
Сделать request-проекцию детерминированной во всех generated артефактах: `operation_map`, transport request model, OpenAPI.

## Scope
- Добавить request metadata (`path/query/body`) в generated `operation_map`.
- Генерировать request transport model из request schema fragment, а не из `{}`.
- Расширить OpenAPI projection: `parameters` (`in: path|query`) и `requestBody`.
- Сохранить корректное поведение для операций без `query` и/или `body`.

## Выходы
- Обновленные генераторы/шаблоны `operation_map`, request-model и OpenAPI.
- Стабильная контрактная проекция request в downstream артефакты.

## Verification Gate
- `uv run pytest tests/unit -k "operation_map or request_model"`
- `uv run pytest tests/integration -k "gen and openapi and request"`
- `uv run pytest tests/integration -k "path and query and body"`
- `uv run ruff check src tests`
- `uv run mypy src`

## Риски
- Расхождение между `operation_map` и OpenAPI проекцией.
- Неправильная обработка опциональных `query/body` в body-less/query-less операциях.

## Definition of Done
- `operation_map` публикует канонические request metadata для каждой операции.
- Generated request model использует контрактный schema fragment и больше не фиксирован как `{}`.
- OpenAPI включает `parameters`/`requestBody` только когда это задано контрактом.
- Повторная генерация на идентичном входе дает идентичный результат.
