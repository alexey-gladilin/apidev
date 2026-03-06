## MODIFIED Requirements
### Requirement: Путь к release state для эволюции контрактов
Система SHALL использовать путь к release state через ключ `evolution.release_state_file` в `.apidev/config.toml` и SHALL не использовать `paths.release_state_file`.

#### Scenario: Переопределение пути release state через конфиг
- **WHEN** пользователь задает `evolution.release_state_file`
- **THEN** команды, работающие с эволюцией контрактов, читают путь release state только из этого ключа
- **AND** путь резолвится по правилам capability `config` (relative-to-`project_dir`, normalize, boundary-check)

### Requirement: Консистентность read-only поведения
Система SHALL применять переопределение `evolution.release_state_file` консистентно во всех релевантных командах; read-only команды SHALL не мутировать release state.

#### Scenario: Выполнение read-only команды
- **WHEN** пользователь запускает read-only команду (например, `validate` или `diff`) с настроенным `evolution.release_state_file`
- **THEN** команда использует переопределенный путь для чтения release state
- **AND** release state файл не создается и не модифицируется этой командой
