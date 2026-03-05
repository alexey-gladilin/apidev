# Поведение: Request Contract Extension

## 1. Root-блок `request`
- Контракт допускает root-поле `request` как нормативное.
- `request` поддерживает только разрешенные подблоки: `path`, `query`, `body`.
- Любые неизвестные поля в `request` или глубже завершают `apidev validate` с fail-fast schema error и указанием точного пути поля.

## 2. `request.path` и согласованность с route path
- Если путь операции содержит `{param}`, эти параметры должны быть описаны в `request.path`.
- Лишние параметры в `request.path`, отсутствующие в route path, запрещены.
- Несогласованность множества параметров приводит к fail-fast validation error до генерации.

### 2.1 Матрица согласованности path params
| Сценарий | Статус | Поведение |
|---|---|---|
| Route path и `request.path` содержат одинаковый набор параметров | Валидно | Генерация продолжается |
| В route path есть параметр, отсутствующий в `request.path` | Невалидно | Fail-fast validation error |
| В `request.path` есть лишний параметр | Невалидно | Fail-fast validation error |
| Операция без `{param}` и без `request.path` | Валидно | Без path parameters в OpenAPI |

## 3. `request.query`
- `request.query` задает декларативную схему query-параметров.
- При наличии `request.query` OpenAPI проекция формирует `parameters` с `in: query`.
- При отсутствии `request.query` query-параметры не добавляются.

## 4. `request.body`
- `request.body` задает schema fragment для request body.
- При наличии `request.body` OpenAPI проекция формирует `requestBody`.
- Для body-less операций `request.body` может отсутствовать без ошибок.

## 5. `operation_map` request metadata
- После `apidev gen` `operation_map` содержит request metadata для `path/query/body`.
- Request metadata является каноническим источником для OpenAPI и request transport-модели.
- Дополнительные эвристики поверх operation metadata не допускаются.

## 6. OpenAPI projection (расширенное поведение)
- OpenAPI строится из полной модели операции: `request + response + errors`.
- Для валидного request-контракта OpenAPI включает:
  - `parameters` для path/query;
  - `requestBody` для body;
  - `responses` для success/error.
- Повторные запуски на одинаковом входе формируют идентичный результат.

## 7. Диагностика и fail-fast
- Ошибки request-валидации останавливают pipeline до этапа генерации.
- Диагностика должна быть стабильной по коду, сообщению и пути поля.
- Partial success для request-ошибок не допускается.
