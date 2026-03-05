## ADDED Requirements

### Requirement: Contract-Level Request Model

`apidev` SHALL поддерживать schema-driven описание request в YAML-контракте через root-блок `request`.

#### Scenario: Root-контракт включает `request`

- **WHEN** контракт содержит блок `request`
- **THEN** `apidev validate` SHALL рассматривать его как нормативный root-поле
- **AND** блок SHALL поддерживать только разрешенную структуру request-контракта

#### Scenario: `request` отсутствует для операций без входных параметров

- **WHEN** операция любого HTTP-метода не требует path/query/body входных данных
- **THEN** отсутствие root-блока `request` SHALL считаться валидным
- **AND** generated OpenAPI SHALL не добавлять `parameters` и `requestBody`

#### Scenario: Unknown поля в `request`

- **WHEN** в `request` или его подблоках присутствуют неизвестные поля
- **THEN** `apidev validate` SHALL завершаться ошибкой schema-валидации
- **AND** diagnostics SHALL указывать точный путь до невалидного поля

### Requirement: Request Schema Fragment Dialect

`apidev` SHALL использовать единый schema dialect для `request.path`, `request.query`, `request.body`, согласованный с уже существующим dialect для `response.body`/`errors[*].body`.

#### Scenario: Допустимая структура request schema fragment

- **WHEN** контракт содержит `request.path`, `request.query` или `request.body`
- **THEN** каждый из этих узлов SHALL быть валидным schema fragment с поддержкой только нормативных ключей (`type`, `properties`, `items`, `required`, `example`)
- **AND** для object-узлов `type: object` SHALL быть обязательным при наличии `properties`
- **AND** значения в `properties.<field>` SHALL быть schema fragments того же dialect

#### Scenario: Невалидный request schema fragment

- **WHEN** в `request.path`, `request.query`, `request.body` или вложенных узлах встречаются неразрешенные ключи, отсутствует обязательный `type`, либо нарушены правила `properties/items/required`
- **THEN** `apidev validate` SHALL завершаться fail-fast schema error
- **AND** diagnostics SHALL содержать стабильный path до невалидного поля

### Requirement: Request Path Parameters Support

`apidev` SHALL поддерживать декларативное описание path parameters и согласованность с HTTP path-шаблоном.

#### Scenario: Path params описаны и соответствуют шаблону пути

- **WHEN** путь контракта содержит placeholder-параметры в формате `{param}`
- **AND** `request.path` описывает те же параметры
- **THEN** контракт SHALL считаться валидным
- **AND** generated OpenAPI SHALL содержать соответствующие `in: path` parameters

#### Scenario: Path params не согласованы с path-шаблоном

- **WHEN** в `request.path` отсутствует параметр из path-шаблона или указан лишний параметр
- **THEN** `apidev validate` SHALL завершаться fail-fast validation error

#### Scenario: Placeholder-путь без `request.path`

- **WHEN** `path` содержит хотя бы один placeholder `{param}`, а `request.path` не задан
- **THEN** `apidev validate` SHALL завершаться fail-fast validation error
- **AND** неявный auto-infer path-params SHALL не выполняться

#### Scenario: Edge-case правила path placeholders

- **WHEN** выполняется сравнение `{param}` из `path` и полей `request.path`
- **THEN** сопоставление имен SHALL быть case-sensitive и выполняться по точному имени без нормализации
- **AND** дубли placeholder-имен в `path` SHALL считаться невалидным контрактом

### Requirement: Request Query Parameters Support

`apidev` SHALL поддерживать декларативное описание query parameters.

#### Scenario: Query params описаны в `request.query`

- **WHEN** контракт содержит `request.query`
- **THEN** generated OpenAPI SHALL проецировать эти параметры в `parameters` с `in: query`
- **AND** generated request-model metadata SHALL включать query schema fragment

#### Scenario: Query params отсутствуют

- **WHEN** операция не требует query-параметров
- **THEN** отсутствие `request.query` SHALL считаться валидным
- **AND** generated OpenAPI SHALL не добавлять лишние query parameters

### Requirement: Request Body Support

`apidev` SHALL поддерживать декларативное описание request body.

#### Scenario: Body описан в `request.body`

- **WHEN** контракт содержит `request.body` schema fragment
- **THEN** generated OpenAPI SHALL содержать `requestBody` для операции
- **AND** generated request-model SHALL использовать schema fragment из `request.body`

#### Scenario: Body отсутствует для body-less операций

- **WHEN** операция не предполагает request body
- **THEN** отсутствие `request.body` SHALL считаться валидным
- **AND** generated OpenAPI SHALL не добавлять `requestBody`

### Requirement: Request Metadata In Operation Map

`apidev` SHALL публиковать request metadata в generated `operation_map`.

#### Scenario: Operation map содержит request metadata

- **WHEN** выполнен `apidev gen`
- **THEN** `operation_map` SHALL включать request metadata (path/query/body schema fragments)
- **AND** эти данные SHALL использоваться генераторами transport/OpenAPI без дополнительных эвристик

### Requirement: Legacy Contract Backward Compatibility

`apidev` SHALL сохранять обратную совместимость для валидных legacy-контрактов, не содержащих root-блок `request`.

#### Scenario: Legacy контракт без `request`

- **WHEN** контракт не содержит `request`, валиден по историческим правилам `method/path/auth/summary/description/response/errors` и не содержит placeholder-параметров в `path`
- **THEN** `apidev validate` SHALL принимать такой контракт без migration-переходника
- **AND** generated OpenAPI SHALL не добавлять `parameters`/`requestBody`, если они не заданы контрактом

### Requirement: Request Validation Diagnostics Contract

Request-related fail-fast валидация SHALL публиковать стабильные machine-readable diagnostics codes в namespace `validation.*`.

#### Scenario: Request validation emits stable diagnostics codes

- **WHEN** `apidev validate` обнаруживает request-related ошибку (`unknown-field`, `schema-invalid`, `path-mismatch`, `missing-request-path`, `duplicate-path-placeholder`)
- **THEN** diagnostics item SHALL содержать обязательные поля `code`, `severity`, `location`, `message`
- **AND** `code` SHALL принадлежать namespace `validation.*` и оставаться детерминированным для одинакового failure mode

### Requirement: Request-Aware OpenAPI Projection

Generated OpenAPI projection SHALL строиться из полной контрактной модели операции (request + response + errors).

#### Scenario: OpenAPI projection включает request и response

- **WHEN** контракт валиден и содержит request/response блоки
- **THEN** generated OpenAPI SHALL включать:
  - `parameters` для path/query
  - `requestBody` для body
  - `responses` для success/error
- **AND** проекция SHALL оставаться детерминированной между повторными запусками
