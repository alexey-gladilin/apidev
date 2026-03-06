## ADDED Requirements

### Requirement: Endpoint Include/Exclude Selection for Code Generation
`apidev gen` SHALL поддерживать выборочную генерацию endpoint-ов через CLI-фильтры include/exclude без нарушения детерминированности generation pipeline.

#### Scenario: Pattern grammar и matching policy детерминированы
- **WHEN** пользователь передает `--include-endpoint <pattern>` или `--exclude-endpoint <pattern>`
- **THEN** `pattern` SHALL интерпретироваться как case-sensitive glob-expression над строками `operation_id` и `contract_relpath`
- **AND** endpoint SHALL считаться matching, если pattern совпал хотя бы с одним из двух идентификаторов (`operation_id OR contract_relpath`)
- **AND** пустая строка pattern SHALL считаться невалидной
- **AND** syntactically malformed glob pattern (например, незакрытый `[` в character-class) SHALL считаться невалидной

#### Scenario: Include-фильтр ограничивает набор endpoint-ов
- **WHEN** пользователь запускает `apidev gen` с одним или несколькими `--include-endpoint <pattern>`
- **THEN** generation SHALL строить план только для endpoint-ов, matching include-pattern набору
- **AND** endpoint-ы вне include-набора SHALL не попадать в effective generation set

#### Scenario: Exclude-фильтр применяется после include
- **WHEN** пользователь запускает `apidev gen` одновременно с `--include-endpoint` и `--exclude-endpoint`
- **THEN** effective endpoint set SHALL рассчитываться по правилу `include -> exclude`
- **AND** endpoint-ы, matching exclude-pattern, SHALL исключаться из итогового набора даже если были включены include-pattern

#### Scenario: Невалидный pattern вызывает fail-fast diagnostics
- **WHEN** пользователь передает синтаксически невалидный pattern в `--include-endpoint` или `--exclude-endpoint`
- **THEN** команда SHALL завершаться с ошибкой
- **AND** diagnostics SHALL содержать детерминированный `code`/`location`/`detail`, позволяющие машинную проверку
- **AND** diagnostics code SHALL принадлежать namespace `generation.*`

#### Scenario: Пустой effective set после фильтрации
- **WHEN** после применения include/exclude фильтров не остается ни одного endpoint-а
- **THEN** `apidev gen` SHALL завершаться с ошибкой валидации фильтра
- **AND** команда SHALL не выполнять apply-запись generated artifacts
- **AND** diagnostics code SHALL принадлежать namespace `generation.*`

#### Scenario: Remove semantics ограничена выбранным endpoint scope
- **WHEN** пользователь запускает `apidev gen` с include/exclude фильтрами
- **THEN** stale-remove SHALL применяться только к generated artifacts, соответствующим effective endpoint set
- **AND** artifacts вне effective endpoint set SHALL не помечаться на удаление только из-за отсутствия endpoint-а в фильтрованном запуске
- **AND** safety boundary удаления SHALL оставаться неизменной относительно базового `apidev gen` контракта

#### Scenario: Backward compatibility без фильтров
- **WHEN** пользователь запускает `apidev gen` без `--include-endpoint` и `--exclude-endpoint`
- **THEN** команда SHALL использовать полный набор endpoint-контрактов как и до изменения
- **AND** повторные запуски на неизменном входе SHALL сохранять byte-stable output
