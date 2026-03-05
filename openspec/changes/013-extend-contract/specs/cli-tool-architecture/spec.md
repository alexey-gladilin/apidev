## ADDED Requirements

### Requirement: Contract-Level Request Model

`apidev` SHALL поддерживать schema-driven описание request в YAML-контракте через root-блок `request`.

#### Scenario: Root-контракт включает `request`

- **WHEN** контракт содержит блок `request`
- **THEN** `apidev validate` SHALL рассматривать его как нормативный root-поле
- **AND** блок SHALL поддерживать только разрешенную структуру request-контракта

#### Scenario: Unknown поля в `request`

- **WHEN** в `request` или его подблоках присутствуют неизвестные поля
- **THEN** `apidev validate` SHALL завершаться ошибкой schema-валидации
- **AND** diagnostics SHALL указывать точный путь до невалидного поля

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

## MODIFIED Requirements

### Requirement: Generated OpenAPI Projection

Generated OpenAPI projection SHALL строиться из полной контрактной модели операции (request + response + errors).

#### Scenario: OpenAPI projection включает request и response

- **WHEN** контракт валиден и содержит request/response блоки
- **THEN** generated OpenAPI SHALL включать:
  - `parameters` для path/query
  - `requestBody` для body
  - `responses` для success/error
- **AND** проекция SHALL оставаться детерминированной между повторными запусками

