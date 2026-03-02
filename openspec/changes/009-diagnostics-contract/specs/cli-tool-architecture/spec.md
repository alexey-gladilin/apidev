## MODIFIED Requirements

### Requirement: MVP Command Surface

CLI SHALL предоставлять минимальные команды для инициализации workspace, валидации контрактов, preview изменений и применения deterministic generation, а также единообразный machine-readable diagnostics contract для `validate`, `diff`, `gen --check`, `gen` при сохранении существующего plain-text UX.

#### Scenario: Init creates tool workspace

- **WHEN** пользователь запускает `apidev init` в целевом проекте
- **THEN** tool SHALL создавать `.apidev/config.toml`, `.apidev/contracts/` и `.apidev/templates/` при их отсутствии

#### Scenario: Validate reports diagnostics without writing output

- **WHEN** пользователь запускает `apidev validate`
- **THEN** tool SHALL парсить все контракты и публиковать diagnostics
- **AND** tool SHALL не записывать generated source files

#### Scenario: Diff previews planned changes

- **WHEN** пользователь запускает `apidev diff`
- **THEN** tool SHALL вычислять детерминированный generation plan
- **AND** tool SHALL публиковать file-level add/update/remove preview без записи файлов

#### Scenario: Generate applies deterministic output

- **WHEN** пользователь запускает `apidev gen`
- **THEN** tool SHALL записывать файлы согласно вычисленному плану
- **AND** повторный запуск с неизменными входами SHALL не создавать дополнительных content changes

#### Scenario: Все ключевые команды публикуют единый diagnostics envelope

- **WHEN** пользователь запускает `apidev validate`, `apidev diff`, `apidev gen --check` или `apidev gen` в machine-readable режиме
- **THEN** команда SHALL возвращать единый JSON envelope c полями верхнего уровня `command`, `summary`, `diagnostics`
- **AND** `drift_status` SHALL присутствовать для `diff`/`gen --check`/`gen`, а `compatibility` SHALL присутствовать для `diff`/`gen --check`/`gen`

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
