# Тестирование: Request Contract Extension

## Цели
- Подтвердить корректную валидацию `request` на уровне схемы и модели.
- Подтвердить согласованность `request.path` с route path.
- Подтвердить корректную проекцию request в `operation_map`, transport и OpenAPI.
- Подтвердить отсутствие регрессии для операций без request-блоков.
- Подтвердить детерминированность артефактов и диагностики.

## Unit-тесты
- Contract schema validation:
  - root `request` допускается;
  - unknown fields в `request` и подблоках отклоняются;
  - корректный путь до невалидного поля в diagnostics.
- Path consistency:
  - полное совпадение параметров route path и `request.path`;
  - missing/extra path params -> fail-fast.
- Query/body fragments:
  - валидный `request.query` и `request.body`;
  - отсутствие `query`/`body` для body-less/query-less операций.
- Contract model mapping:
  - `EndpointContract` получает корректные request-поля.
- Operation metadata projection:
  - path/query/body fragments присутствуют в operation_map и стабильны по структуре.

## Integration-тесты
- `apidev validate`:
  - успешный сценарий с полным `request`;
  - негативные сценарии unknown fields/path mismatch.
- `apidev gen`:
  - request transport model формируется из контракта, а не из пустого `{}`.
  - operation_map содержит request metadata для каждой операции.
- OpenAPI projection:
  - `parameters` (path/query) и `requestBody` создаются из request-контракта;
  - для операций без query/body соответствующие блоки отсутствуют;
  - `responses` остаются корректными и совместимыми.

## Regression-тесты
- Контракты без `request` (legacy-сценарий) продолжают обрабатываться без функциональной деградации, если это допускается правилами change.
- Существующая генерация `response/errors` не меняет семантику.
- Порядок операций и стабильность сериализации не изменяются.

## Determinism-проверки
- Идентичный вход (`config + contracts`) дает байтово-идентичные generated artifacts.
- Diagnostics для идентичных ошибок остаются стабильными по `code/message/context`.

## Acceptance mapping
- Contract-Level Request Model -> unit schema + integration validate.
- Request Path Parameters Support -> unit/integration path consistency.
- Request Query Parameters Support -> integration OpenAPI parameters + operation_map metadata.
- Request Body Support -> integration OpenAPI requestBody + request-model projection.
- Request Metadata in Operation Map -> unit/integration metadata checks.
- Modified OpenAPI Projection -> integration OpenAPI end-to-end + determinism checks.
