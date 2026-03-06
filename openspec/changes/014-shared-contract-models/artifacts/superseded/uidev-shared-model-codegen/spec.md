## ADDED Requirements

### Requirement: Shared Model Graph Normalization
Система SHALL интерпретировать входные контракты с reusable-моделями как граф моделей и ссылок, а не только как набор независимых inline-деревьев операций.

#### Scenario: Shared references are resolved before rendering
- **WHEN** `uidev` загружает контракт, содержащий shared models и `ref`
- **THEN** до этапа render формируется resolved model graph с проверенными зависимостями и scope information

### Requirement: Single Materialization of Shared Models
Система SHALL генерировать shared-модели и соответствующие runtime schema artifacts один раз на generator scope, а не дублировать их в каждом operation module.

#### Scenario: Shared pagination model is emitted once
- **WHEN** несколько операций используют одну и ту же shared-модель пагинации
- **THEN** generated output содержит единственную materialization этой модели в shared area и imports из operation-level файлов

### Requirement: Operation Modules Import Shared Symbols
Система SHALL использовать стабильные импорты shared symbols в operation-level generated files вместо повторной генерации идентичного shared shape.

#### Scenario: Operation schema imports shared schema
- **WHEN** request или response операции содержит ссылку на shared model
- **THEN** соответствующий generated operation module импортирует shared type/schema symbol и не создает дубликат локально

### Requirement: Backward-Compatible Mixed Mode
Система SHALL поддерживать переходный mixed mode, в котором inline-only контракты продолжают обрабатываться без обязательной миграции на shared models.

#### Scenario: Old inline contract still generates successfully
- **WHEN** контракт не использует `models/ref` и описывает все структуры inline
- **THEN** `uidev` продолжает успешно выполнять validate/plan/render без требования немедленного перехода на новый формат

### Requirement: Deterministic Shared Output Layout
Система SHALL формировать shared generated artifacts и экспортный порядок детерминированно для идентичного входного графа моделей.

#### Scenario: Repeated generation produces identical shared files
- **WHEN** один и тот же набор контрактов с shared-моделями генерируется повторно
- **THEN** shared files, import order и export order остаются идентичными между прогонами
