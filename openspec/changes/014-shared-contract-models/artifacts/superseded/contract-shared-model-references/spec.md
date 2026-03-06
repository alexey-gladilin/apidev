## ADDED Requirements

### Requirement: Shared Contract Models
Система SHALL позволять объявлять переиспользуемые именованные модели контракта как first-class artifact, доступный нескольким операциям без дублирования inline-shape описаний.

#### Scenario: Shared model is declared once and reused in multiple operations
- **WHEN** автор контракта объявляет shared-модель в registry `models`
- **AND** две или более операции ссылаются на нее
- **THEN** контракт выражает общую семантическую модель один раз и не требует повторного описания одинакового объекта в каждой операции

### Requirement: Nested Model References
Система SHALL поддерживать ссылки на shared-модели не только на верхнем уровне request/response, но и во вложенных properties и других составных узлах.

#### Scenario: Shared model is referenced from nested request property
- **WHEN** request body содержит свойство `pagination` или `sort` как вложенный объект
- **AND** это свойство оформлено через `ref`
- **THEN** ссылка валидно разрешается к shared-модели без необходимости inline-описания структуры свойства

### Requirement: Scope-Safe Model Resolution
Система SHALL различать shared models и operation-local models и обеспечивать корректную область видимости для ссылок.

#### Scenario: Operation-local model cannot leak into shared scope
- **WHEN** shared-модель или другая операция пытается сослаться на operation-local модель
- **THEN** validation завершается ошибкой с явной диагностикой нарушения scope boundaries

### Requirement: Deterministic Reference Validation
Система SHALL детерминированно разрешать ссылки на модели и отклонять неоднозначные или некорректные ссылки.

#### Scenario: Missing or ambiguous reference is rejected
- **WHEN** контракт содержит `ref` на отсутствующую модель или неоднозначное имя
- **THEN** validate pipeline завершается ошибкой с указанием проблемной ссылки и ожидаемого способа разрешения

### Requirement: Unsupported Cycles Are Rejected Explicitly
Система SHALL явно отклонять циклические зависимости между моделями, если текущая версия tooling не поддерживает их безопасную materialization.

#### Scenario: Model cycle is detected during validation
- **WHEN** две или более модели формируют запрещенный цикл ссылок
- **THEN** validation сообщает о цикле до этапа кодогенерации и предотвращает неоднозначный output
