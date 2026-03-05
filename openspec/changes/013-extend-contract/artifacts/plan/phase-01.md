# Phase 01: Контрактная схема и модель request

## Цель фазы
Сделать `request` нормативной частью контракта с strict/fail-fast валидацией и согласованием `request.path` с route template.

## Scope
- Добавить root-блок `request` в schema rules.
- Разрешить только `request.path`, `request.query`, `request.body`; запретить unknown fields.
- Добавить проверку согласованности `request.path` и `{param}` в `path`.
- Расширить контрактную модель (`EndpointContract`) request-полями.

## Выходы
- Обновленная схема валидации контракта request-ветки.
- Обновленная доменная модель контракта с request-полями.
- Предсказуемые diagnostics для request-ошибок и path mismatch.

## Verification Gate
- `uv run pytest tests/unit -k "contract_schema or request or path"`
- `uv run pytest tests/integration -k "validate and request"`
- `uv run ruff check src tests`
- `uv run mypy src`

## Риски
- Слишком строгая валидация может сломать существующие контракты с неформальным request-описанием.
- Ошибки сравнения path-параметров могут давать ложные блокировки генерации.

## Definition of Done
- `request` валиден как root-блок и проходит strict-schema проверки.
- Unknown fields в request-ветке стабильно отклоняются с точным path в diagnostics.
- Несогласованные path params завершают `apidev validate` fail-fast ошибкой.
- `EndpointContract` содержит request-поля и используется без эвристик.
