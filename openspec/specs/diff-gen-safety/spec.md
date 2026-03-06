# diff-gen-safety Specification

## Purpose
TBD - created by archiving change 004-diff-gen-safety. Update Purpose after archive.
## Requirements
### Requirement: Validate-First Safety Pipeline
`apidev diff` и `apidev gen` SHALL выполнять preflight validation перед вычислением diff-плана и перед применением изменений.

#### Scenario: Validation failure blocks diff and generation
- **WHEN** входные контракты или конфигурация не проходят validation
- **THEN** `apidev diff` и `apidev gen` SHALL завершаться с ошибкой без попытки вычисления/применения write-плана
- **AND** оператор SHALL получать детерминированный failure-signal для CI/pipeline
- **AND** CLI exit semantics SHALL соответствовать контракту: exit `1` для validation/business failure, exit `0` только для успешного завершения команды

### Requirement: Drift Governance Modes
Система SHALL поддерживать раздельные режимы drift governance для preview и apply.

#### Scenario: Diff mode is read-only and reports planned changes
- **WHEN** оператор запускает `apidev diff` на валидном проекте
- **THEN** команда SHALL вычислять и отображать diff-план без записи файлов
- **AND** результат SHALL быть пригоден для CI drift-gate без мутации workspace
- **AND** drift-status SHALL быть нормирован как `drift`, `no-drift` или `error` (для ошибок пайплайна)
- **AND** exit semantics SHALL быть `0` для `drift`/`no-drift` и `1` для `error`

#### Scenario: Check mode detects drift without writes
- **WHEN** оператор запускает `apidev gen --check`
- **THEN** команда SHALL определять наличие drift на основе diff-плана
- **AND** команда SHALL не записывать изменения в generated artifacts
- **AND** drift-status SHALL быть нормирован как `drift`, `no-drift` или `error`
- **AND** exit semantics SHALL быть `1` для `drift`/`error` и `0` для `no-drift`

#### Scenario: Apply mode writes only planned additive updates
- **WHEN** оператор запускает `apidev gen` без check-mode
- **THEN** система SHALL применять только разрешенные операции записи `ADD` и `UPDATE` из diff-плана
- **AND** результат SHALL сообщать количество примененных изменений и итоговый drift-status
- **AND** drift-status SHALL быть нормирован как `drift`, `no-drift` или `error`, где успешный apply для актуального состояния интерпретируется как `no-drift`
- **AND** exit semantics SHALL быть `0` для успешного apply и `1` для `error`

### Requirement: Generated Write Boundary Safety
Система SHALL гарантировать, что операции записи ограничены generated-root и не затрагивают manual-owned зону.

#### Scenario: Writes outside generated root are rejected
- **WHEN** write-target выходит за пределы configured generated-root
- **THEN** операция записи SHALL быть отклонена с явной ошибкой safety boundary
- **AND** manual-owned файлы SHALL оставаться неизменными

#### Scenario: Generated root cannot be overwritten as a file
- **WHEN** write-target совпадает с путем generated-root как файла
- **THEN** операция SHALL завершаться ошибкой
- **AND** частичные изменения SHALL не применяться (если возникает boundary-error, команда не должна подтверждать успешное применение)

### Requirement: Deterministic Drift Signal
Diff/generate pipeline SHALL быть детерминированным для неизменных входных контрактов.

#### Scenario: Stable planning output for unchanged contracts
- **WHEN** diff/generate запускаются повторно на одном и том же наборе контрактов
- **THEN** вычисленный diff-план SHALL оставаться эквивалентным по содержанию и порядку
- **AND** повторный apply-run SHALL не создавать новых изменений

#### Scenario: Contract metadata changes trigger deterministic drift
- **WHEN** меняется контрактно-значимая metadata, влияющая на generated artifacts
- **THEN** diff/check SHALL детектировать drift
- **AND** после apply-run и повторной проверки drift SHALL отсутствовать

