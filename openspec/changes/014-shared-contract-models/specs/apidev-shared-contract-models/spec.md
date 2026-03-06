## ADDED Requirements

### Requirement: Shared Contract Models
Система SHALL позволять объявлять переиспользуемые именованные модели контракта как first-class artifact в отдельном shared-model contract file, доступном нескольким операциям без дублирования inline-shape описаний.

#### Scenario: Shared model is declared once and reused in multiple operations
- **WHEN** автор контракта объявляет shared-модель отдельным файлом в shared models directory
- **AND** две или более операции ссылаются на нее
- **THEN** контракт выражает общую семантическую модель один раз и не требует повторного описания одинакового объекта в каждой операции

### Requirement: Contract Kind And Location Are Explicit
Система SHALL явно различать API operation contracts и shared model contracts по расположению и типу контракта.

#### Scenario: Shared model file is distinguishable from API contract file
- **WHEN** аналитик, разработчик или generator tooling читает YAML-файл контракта
- **THEN** по директории размещения и root field `contract_type` однозначно определяется, является ли файл API operation contract или shared model contract

### Requirement: Nested Model References
Система SHALL поддерживать ссылки на shared-модели не только на верхнем уровне request/response, но и во вложенных properties и других составных узлах.

#### Scenario: Shared model is referenced from nested request property
- **WHEN** request body содержит свойство `pagination` или `sort` как вложенный объект
- **AND** это свойство оформлено через `$ref`
- **THEN** ссылка валидно разрешается к shared-модели без необходимости inline-описания структуры свойства

### Requirement: Scope-Safe Model Resolution
Система SHALL различать shared models и operation-local models и обеспечивать корректную область видимости для ссылок.

#### Scenario: Operation-local model cannot leak into shared scope
- **WHEN** shared-модель или другая операция пытается сослаться на operation-local модель
- **THEN** validation завершается ошибкой с явной диагностикой нарушения scope boundaries

### Requirement: Deterministic Reference Validation
Система SHALL детерминированно разрешать ссылки на модели и отклонять неоднозначные или некорректные ссылки.

#### Scenario: Missing or ambiguous reference is rejected
- **WHEN** контракт содержит `$ref` или shorthand `$...` на отсутствующую модель или неоднозначное имя
- **THEN** validate pipeline завершается ошибкой с указанием проблемной ссылки и ожидаемого способа разрешения

### Requirement: Contract Validation Uses Pydantic
Система SHALL валидировать operation contracts и shared model contracts через Pydantic-based contract models в Python validation pipeline.

#### Scenario: Shared model contract passes Pydantic validation before semantic checks
- **WHEN** `apidev validate` читает YAML shared model contract
- **THEN** файл сначала парсится и валидируется соответствующей Pydantic-моделью контракта, а затем участвует в cross-file semantic validation

### Requirement: Namespace Is Derived From Shared Model Location
Система SHALL выводить namespace shared model из имени директории, в которой расположен shared model contract file, а не из дублирующего root-поля внутри файла.

#### Scenario: Namespace is resolved from directory name
- **WHEN** shared model contract расположен по пути `.apidev/models/common/pagination_request.yaml`
- **THEN** namespace модели определяется как `common`, даже если root-level поле `namespace` отсутствует

### Requirement: Unsupported Cycles Are Rejected Explicitly
Система SHALL явно отклонять циклические зависимости между моделями, если текущая версия tooling не поддерживает их безопасную materialization.

#### Scenario: Model cycle is detected during validation
- **WHEN** две или более модели формируют запрещенный цикл ссылок
- **THEN** validation сообщает о цикле до этапа кодогенерации и предотвращает неоднозначный output

### Requirement: Validate Performs Graph-Aware Cycle Detection
Система SHALL использовать `apidev validate` как нормативную точку проверки graph invariants, включая цикл ссылок и другие нарушения графа зависимостей.

#### Scenario: Validate reports shared model cycle
- **WHEN** `apidev validate` обрабатывает контракты с циклом между shared models
- **THEN** команда завершается ошибкой и возвращает диагностику, содержащую путь цикла в machine-readable виде

### Requirement: Contract Dependency Graph Is Introspectable
Система SHALL предоставлять CLI-возможность построения и вывода dependency graph для operation contracts, shared models и их ссылок.

#### Scenario: User asks which contracts use shared model
- **WHEN** пользователь запрашивает обратные зависимости для shared model
- **THEN** CLI возвращает список operation contracts и/или shared models, использующих указанную shared model

### Requirement: Graph Output Supports Machine Processing
Система SHALL поддерживать стандартизированный machine-readable формат вывода dependency graph для автоматизации и внешних инструментов.

#### Scenario: CI requests graph in JSON format
- **WHEN** dependency graph запрашивается с machine-readable output option
- **THEN** CLI возвращает JSON со списком узлов, ребер и summary-метаданными
