# safety-drift Specification

## Purpose
TBD - created by archiving change 006-safety-drift. Update Purpose after archive.
## Requirements
### Requirement: REMOVE операция в generation plan
Система SHALL формировать `REMOVE`-операции в generation plan для stale generated artifacts, которые больше не соответствуют текущему набору контрактов.

#### Scenario: Diff формирует REMOVE для устаревшего generated файла
- **WHEN** в generated root существует артефакт для операции, отсутствующей в актуальных контрактах
- **THEN** `apidev diff` SHALL включать `REMOVE` для этого артефакта в детерминированном плане
- **AND** `REMOVE` SHALL быть ограничен только путями внутри configured generated root

#### Scenario: План не помечает REMOVE за пределами generated root
- **WHEN** путь stale файла резолвится вне configured generated root
- **THEN** система SHALL отклонять такой `REMOVE` как safety violation
- **AND** diagnostics SHALL явно указывать нарушение write-boundary

### Requirement: Drift семантика удаления для diff и gen --check
`REMOVE` SHALL участвовать в drift-детекции во всех read-only режимах.

#### Scenario: Diff сообщает drift при наличии REMOVE
- **WHEN** план содержит только `REMOVE` без `ADD/UPDATE`
- **THEN** `apidev diff` SHALL сообщать `Drift status: drift`
- **AND** `apidev diff` SHALL завершаться с exit `0` как preview-режим

#### Scenario: Gen check фейлится при REMOVE drift
- **WHEN** `apidev gen --check` обнаруживает хотя бы один `REMOVE`
- **THEN** drift-status SHALL быть `drift`
- **AND** команда SHALL завершаться с exit `1`

### Requirement: Apply semantics для REMOVE в apidev gen
В apply-режиме `apidev gen` SHALL выполнять `REMOVE` вместе с разрешенными `ADD/UPDATE`.

#### Scenario: Gen применяет REMOVE внутри generated root
- **WHEN** `apidev gen` запускается на плане, содержащем `REMOVE`
- **THEN** stale generated artifacts SHALL удаляться детерминированно
- **AND** успешный apply SHALL завершаться статусом `no-drift` и exit `0`

#### Scenario: Ошибка удаления отражается как pipeline error
- **WHEN** удаление не может быть выполнено из-за filesystem/safety ошибки
- **THEN** система SHALL возвращать drift-status `error`
- **AND** команда SHALL завершаться с exit `1`

### Requirement: Deterministic ordering и diagnostics для REMOVE
Система SHALL обеспечивать детерминированный порядок `REMOVE`-операций и воспроизводимые diagnostics.

Канонический каталог diagnostic codes для remove-сценариев SHALL быть фиксирован:
- `remove-conflict` — stale artifact отсутствует к моменту apply;
- `remove-boundary-violation` — путь remove-операции выходит за `generated root`.

Минимальный machine-readable формат diagnostics SHALL быть фиксирован для обоих кодов:
- `code` (string, из канонического каталога);
- `location` (string, filesystem path или logical location);
- `detail` (string, стабильное человеко-читаемое пояснение).

#### Scenario: Повторный diff даёт одинаковый REMOVE-план
- **WHEN** входные контракты и состояние generated root не изменяются
- **THEN** `apidev diff` SHALL выдавать эквивалентный список `REMOVE` по составу и порядку
- **AND** diagnostics SHALL быть стабильны между повторными запусками

#### Scenario: Conflict diagnostics фиксированы для remove-case
- **WHEN** stale artifact уже отсутствует к моменту apply или нарушает boundary-policy
- **THEN** система SHALL публиковать `remove-conflict` или `remove-boundary-violation` из канонического каталога
- **AND** diagnostics SHALL содержать поля `code`, `location`, `detail` в machine-readable формате, пригодном для CI triage

### Requirement: Scaffold-aware REMOVE precedence
Для scaffold subtree система SHALL применять scaffold-aware remove policy как уточнение `REMOVE`-семантики внутри generated root.

#### Scenario: Scaffold subtree is kept when scaffold mode is enabled
- **WHEN** effective scaffold mode resolved as enabled (`--scaffold` or `generator.scaffold = true`)
- **AND** stale candidate path belongs to `<generated_dir>/<scaffold_dir>/`
- **THEN** `apidev diff` SHALL NOT планировать `REMOVE` для этого пути
- **AND** базовые safety diagnostics `remove-conflict`/`remove-boundary-violation` SHALL оставаться неизменными

#### Scenario: Scaffold subtree is removable when scaffold mode is disabled
- **WHEN** effective scaffold mode resolved as disabled (`--no-scaffold` or `generator.scaffold = false`)
- **AND** stale candidate path belongs to `<generated_dir>/<scaffold_dir>/`
- **THEN** `apidev diff` SHALL планировать `REMOVE` для этого пути
- **AND** remove semantics SHALL оставаться ограниченными write-boundary внутри generated root

