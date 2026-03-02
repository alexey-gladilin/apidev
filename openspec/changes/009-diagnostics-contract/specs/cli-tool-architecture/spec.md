## MODIFIED Requirements

### Requirement: MVP Command Surface

CLI SHALL предоставлять единообразный machine-readable diagnostics contract для основных режимов `validate`, `diff`, `gen --check`, `gen` при сохранении существующего plain-text UX.

#### Scenario: Все ключевые команды публикуют единый diagnostics envelope

- **WHEN** пользователь запускает `apidev validate`, `apidev diff`, `apidev gen --check` или `apidev gen` в machine-readable режиме
- **THEN** команда SHALL возвращать единый JSON envelope c полями верхнего уровня `command`, `summary`, `diagnostics`
- **AND** `drift_status` SHALL присутствовать для `diff`/`gen --check`/`gen`, а `compatibility` SHALL присутствовать для `diff`/`gen`

#### Scenario: Базовые поля diagnostics стабилизированы для CI

- **WHEN** любая команда публикует diagnostics item
- **THEN** item SHALL содержать обязательные поля `code`, `severity`, `location`, `message`
- **AND** item MAY содержать опциональные стандартизированные поля `category`, `detail`, `source`, `rule`, `hint`

#### Scenario: Таксономия diagnostics codes унифицирована

- **WHEN** система эмитит diagnostic code
- **THEN** code SHALL принадлежать одному из namespace: `validation.`*, `compatibility.*`, `generation.*`, `runtime.*`, `config.*`
- **AND** код SHALL оставаться детерминированным для одинакового входа и одинакового failure mode

#### Scenario: Drift и policy семантика не меняется при hardening diagnostics

- **WHEN** пользователь запускает `apidev diff`, `apidev gen --check`, `apidev gen` после внедрения unified diagnostics contract
- **THEN** drift-status/exit code SHALL сохранять действующую матрицу поведения
- **AND** compatibility policy gate (`warn|strict`) SHALL сохранять текущую blocking семантику

#### Scenario: Plain-text UX остается совместимым

- **WHEN** пользователь запускает команды без machine-readable флага
- **THEN** CLI SHALL выводить человеко-читаемые diagnostics и статусные сообщения
- **AND** формат вывода SHALL оставаться пригодным для ручного triage без обязательного JSON parsing

