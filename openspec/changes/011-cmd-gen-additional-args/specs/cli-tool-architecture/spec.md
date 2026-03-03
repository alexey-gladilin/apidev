## ADDED Requirements

### Requirement: Endpoint Include/Exclude Selection for Code Generation
`apidev gen` SHALL поддерживать выборочную генерацию endpoint-ов через CLI-фильтры include/exclude без нарушения детерминированности generation pipeline.

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
- **AND** diagnostics SHALL содержать детерминированный код и location, позволяющие машинную проверку

#### Scenario: Пустой effective set после фильтрации
- **WHEN** после применения include/exclude фильтров не остается ни одного endpoint-а
- **THEN** `apidev gen` SHALL завершаться с ошибкой валидации фильтра
- **AND** команда SHALL не выполнять apply-запись generated artifacts

#### Scenario: Backward compatibility без фильтров
- **WHEN** пользователь запускает `apidev gen` без `--include-endpoint` и `--exclude-endpoint`
- **THEN** команда SHALL использовать полный набор endpoint-контрактов как и до изменения
- **AND** повторные запуски на неизменном входе SHALL сохранять byte-stable output
