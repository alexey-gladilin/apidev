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
- **WHEN** policy указана одновременно в CLI и в `.apidev/config.toml`
- **THEN** значение из CLI SHALL иметь более высокий приоритет, чем значение из файла конфигурации
- **AND** diagnostics SHALL отражать фактически применённую policy

#### Scenario: Термин drift интерпретируется по каноничному CLI-контракту
- **WHEN** `apidev gen --check` или `apidev diff` формируют drift status
- **THEN** система SHALL использовать нормализованные значения `drift|no-drift|error`
- **AND** `drift` SHALL означать расхождение между ожидаемым generated output и текущими generated artifacts согласно `docs/reference/cli-contract.md` и `docs/reference/glossary.md`

### Requirement: Формальный deprecation lifecycle и release state
Система SHALL обеспечивать формальный deprecation lifecycle (`active -> deprecated -> removed`) с релизным состоянием, достаточным для проверки deprecation window.

#### Scenario: Deprecated элемент отслеживается до удаления
- **WHEN** элемент контракта помечается как `deprecated`
- **THEN** diagnostics и generated metadata SHALL отображать deprecation status
- **AND** lifecycle state SHALL сохраняться между последующими запусками diff/generate

#### Scenario: Release state использует монотонный номер релиза
- **WHEN** система загружает release state для policy checks
- **THEN** release state SHALL включать обязательный `release_number` (integer, монотонно возрастающий)
- **AND** release state MAY включать `git_commit`, `released_at` (UTC) и `tag` как опциональные metadata для трассировки

### Requirement: Контракт хранения release state и границы ответственности
Система SHALL использовать явный источник истины для release state и SHALL исключать неявные side effects в read-only режимах.

#### Scenario: Источник истины задаётся через конфиг с документированным default
- **WHEN** пользователь не задаёт override для release state storage
- **THEN** система SHALL читать release state из `.apidev/release-state.json` по умолчанию
- **AND** путь MAY быть переопределён через `.apidev/config.toml` в секции `evolution.release_state_file`

#### Scenario: Формат release state фиксирован и валидируется
- **WHEN** система читает `.apidev/release-state.json`
- **THEN** файл SHALL быть JSON-объектом формата:
  `{ "release_number": <int>=1..N, "baseline_ref": "<git-tag|git-sha>", "released_at": "<RFC3339 UTC>"?, "git_commit": "<40-hex>"?, "tag": "<string>"? }`
- **AND** при нарушении формата система SHALL возвращать ошибку конфигурации с указанием некорректного поля

#### Scenario: Read-only режимы не модифицируют release state
- **WHEN** запускается `apidev diff` или `apidev gen --check`
- **THEN** система SHALL NOT изменять release state storage
- **AND** любые ошибки чтения/валидации release state SHALL отражаться в diagnostics без скрытой записи на диск

### Requirement: Baseline snapshot для compatibility classification
Система SHALL выполнять compatibility classification только на основе сравнения текущей нормализованной API-модели с baseline snapshot, полученным из общего (team-wide) источника истины.

#### Scenario: Источник истины baseline — VCS/CI, а не локальная рабочая директория
- **WHEN** выполняется compare для `apidev diff` или `apidev gen --check`
- **THEN** baseline snapshot SHALL резолвиться через `baseline_ref` (git tag или git commit) из release state либо явный CLI override `--baseline-ref`
- **AND** одинаковый `baseline_ref` SHALL давать одинаковый baseline на разных машинах разработчиков

#### Scenario: Формат baseline snapshot фиксирован и детерминирован
- **WHEN** система читает baseline snapshot, резолвленный из `baseline_ref`
- **THEN** snapshot SHALL быть JSON-объектом с нормализованным представлением API (operations, request/response schemas, errors, deprecation metadata)
- **AND** сериализация SHALL быть детерминированной для одинаковых входных контрактов

#### Scenario: Классификация основана на сравнении baseline и текущего состояния
- **WHEN** запускается `apidev diff` или `apidev gen --check`
- **THEN** compatibility classification SHALL вычисляться как `compare(current_normalized_model, baseline_snapshot)`
- **AND** diagnostics SHALL содержать `baseline_ref`, использованный для сравнения

#### Scenario: Локальная потеря baseline не ломает compare при доступном VCS
- **WHEN** локальный cache baseline snapshot отсутствует
- **THEN** система SHALL пытаться восстановить baseline через `baseline_ref` из VCS/CI-источника
- **AND** успешное восстановление SHALL NOT считаться ошибкой policy

#### Scenario: Нерезолвимый baseline обрабатывается явно
- **WHEN** `baseline_ref` отсутствует, нерезолвим или snapshot невалиден
- **THEN** система SHALL возвращать явный diagnostic code `baseline-missing` или `baseline-invalid`
- **AND** в policy `strict` команда SHALL завершаться с non-zero exit code

### Requirement: Конфигурируемое deprecation window
Система SHALL использовать конфигурируемый параметр `grace_period_releases` для проверки допустимости удаления deprecated элементов.

#### Scenario: Параметр окна задаётся в конфигурации evolution
- **WHEN** пользователь задаёт `grace_period_releases` в `.apidev/config.toml`
- **THEN** система SHALL читать параметр из секции `evolution.grace_period_releases`
- **AND** это значение SHALL использоваться во всех deprecation-window checks для `diff` и `gen --check`

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
- **THEN** система SHALL использовать default значение `2`
- **AND** при значении меньше 1 система SHALL возвращать ошибку конфигурации с явным указанием недопустимого значения
