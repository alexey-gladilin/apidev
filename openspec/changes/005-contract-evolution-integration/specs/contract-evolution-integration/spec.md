## ADDED Requirements

### Requirement: Классификация совместимости для эволюции контрактов
`apidev diff` и `apidev gen --check` SHALL классифицировать обнаруженные изменения контрактов по категориям совместимости и выводить эту классификацию в diagnostics.

#### Scenario: Diff выводит группы breaking и non-breaking изменений
- **WHEN** пользователь запускает `apidev diff` после изменения контрактов
- **THEN** вывод SHALL содержать категоризированную сводку совместимости
- **AND** каждое обнаруженное изменение SHALL быть отнесено к детерминированной категории совместимости

#### Scenario: Check mode завершает команду с ошибкой при active strict policy
- **WHEN** включена policy `strict` и `apidev gen --check` обнаруживает изменения категории `breaking`
- **THEN** команда SHALL возвращать non-zero exit code
- **AND** diagnostics SHALL явно перечислять причины breaking classification

### Requirement: Контракт конфигурации compatibility policy
Система SHALL поддерживать явный конфигурационный контракт для compatibility policy с предсказуемыми defaults и приоритетами источников настроек.

#### Scenario: Policy по умолчанию не ломает обратную совместимость workflow
- **WHEN** пользователь не задаёт compatibility policy ни в CLI, ни в конфиге
- **THEN** система SHALL использовать policy `warn` по умолчанию
- **AND** `apidev gen --check` SHALL завершаться с ошибкой только при drift, но не из-за одних лишь `breaking` diagnostics

#### Scenario: CLI имеет приоритет над файлом конфигурации
- **WHEN** policy указана одновременно в CLI и в `apidev.toml`
- **THEN** значение из CLI SHALL иметь более высокий приоритет, чем значение из файла конфигурации
- **AND** diagnostics SHALL отражать фактически применённую policy

### Requirement: Optional read-only dbspec integration
APIDev SHALL поддерживать optional integration с `dbspec` как read-only источником schema hints без обязательной зависимости от `dbspec` для baseline workflow.

#### Scenario: Workflow остаётся работоспособным без dbspec
- **WHEN** артефакты `dbspec` недоступны
- **THEN** `apidev validate`, `apidev diff` и `apidev gen` SHALL продолжать работу в baseline mode
- **AND** инструмент SHALL NOT требовать `dbspec` как обязательную зависимость

#### Scenario: Данные контракта имеют приоритет над внешними hints
- **WHEN** и contract fields, и optional dbspec hints задают значение одного schema attribute
- **THEN** SHALL применяться детерминированная merge policy
- **AND** значение, объявленное в контракте, SHALL иметь приоритет

### Requirement: Формальный deprecation lifecycle и release state
Система SHALL обеспечивать формальный deprecation lifecycle (`active -> deprecated -> removed`) с релизным состоянием, достаточным для проверки deprecation window.

#### Scenario: Deprecated элемент отслеживается до удаления
- **WHEN** элемент контракта помечается как `deprecated`
- **THEN** diagnostics и generated metadata SHALL отображать deprecation status
- **AND** lifecycle state SHALL сохраняться между последующими запусками diff/generate

#### Scenario: Release state использует монотонный номер релиза
- **WHEN** система фиксирует очередной релиз для policy checks
- **THEN** release state SHALL включать обязательный `release_number` (integer, монотонно возрастающий)
- **AND** release state MAY включать `git_commit`, `released_at` (UTC) и `tag` как опциональные metadata для трассировки

### Requirement: Конфигурируемое deprecation window
Система SHALL использовать конфигурируемый параметр `grace_period_releases` для проверки допустимости удаления deprecated элементов.

#### Scenario: Удаление раньше окна классифицируется как breaking
- **WHEN** элемент удалён и выполняется условие `current_release_number - deprecated_since_release_number < grace_period_releases`
- **THEN** изменение SHALL классифицироваться как `breaking`
- **AND** diagnostics SHALL содержать детали policy violation с фактическими числовыми значениями окна

#### Scenario: Удаление после окна не классифицируется как breaking по policy-причине
- **WHEN** элемент удалён и выполняется условие `current_release_number - deprecated_since_release_number >= grace_period_releases`
- **THEN** изменение SHALL NOT классифицироваться как `breaking` только по причине нарушения deprecation window
- **AND** diagnostics MAY содержать информационное сообщение об успешном соблюдении deprecation policy

#### Scenario: Значение окна по умолчанию и валидация параметра
- **WHEN** `grace_period_releases` не задан в конфигурации
- **THEN** система SHALL использовать documented default значение
- **AND** при значении меньше 1 система SHALL возвращать ошибку конфигурации с явным указанием недопустимого значения
