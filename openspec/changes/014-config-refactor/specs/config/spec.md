## ADDED Requirements
### Requirement: Каноническая структура `.apidev/config.toml`
Система SHALL использовать секционную структуру конфигурации с явным разделением зон ответственности: `paths`, `inputs`, `generator`, `evolution`, `openapi`.

#### Scenario: Конфиг соответствует канонической секционной модели
- **WHEN** пользователь предоставляет валидный `.apidev/config.toml`
- **THEN** загрузчик конфигурации интерпретирует ключи только из канонических секций
- **AND** команды `validate`, `diff`, `gen`, `init` используют единый resolved config snapshot

### Requirement: Нормативный набор ключей нового формата
Система SHALL реализовать следующий набор секций и ключей в `.apidev/config.toml`:
- `paths.templates_dir`
- `paths.release_state_file`
- `inputs.contracts_dir`
- `inputs.shared_models_dir`
- `generator.generated_dir`
- `generator.postprocess`
- `generator.scaffold`
- `generator.scaffold_dir`
- `generator.scaffold_write_policy`
- `evolution.compatibility_policy`
- `evolution.grace_period_releases`
- `openapi.include_extensions`

#### Scenario: Конфиг содержит все нормативные ключи
- **WHEN** пользователь использует новый формат конфига
- **THEN** система валидирует и применяет все перечисленные ключи
- **AND** отсутствие unknown/legacy ключей не вызывает диагностик ошибок

### Requirement: Отсутствие поля `version` в конфигурационном контракте
Система SHALL не использовать поле `version` в `.apidev/config.toml`.

#### Scenario: Конфиг без `version`
- **WHEN** пользователь запускает команды с конфигом, не содержащим `version`
- **THEN** система выполняет загрузку и валидацию без ошибок, связанных с версией

#### Scenario: В конфиг добавлен `version`
- **WHEN** пользователь указывает поле `version` в `.apidev/config.toml`
- **THEN** система завершает загрузку fail-fast ошибкой валидации
- **AND** diagnostics указывает недопустимый ключ и ожидаемую структуру

### Requirement: Fail-fast валидация без backward compatibility
Система SHALL поддерживать только новый формат конфигурации и завершаться ошибкой при использовании legacy-структур.

#### Scenario: Использован legacy-ключ
- **WHEN** в конфиге присутствует ключ, не входящий в новый контракт
- **THEN** загрузка завершается ошибкой валидации до бизнес-операций
- **AND** diagnostics содержит путь до ключа и сообщение о нарушении контракта
