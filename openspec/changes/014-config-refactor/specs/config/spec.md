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
- `inputs.contracts_dir`
- `inputs.shared_models_dir`
- `generator.generated_dir`
- `generator.postprocess`
- `generator.scaffold`
- `generator.scaffold_dir`
- `generator.scaffold_write_policy`
- `evolution.release_state_file`
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

### Requirement: Детерминированная валидация неизвестных секций и ключей
Система SHALL принимать только явно объявленные секции и ключи канонического контракта; любая лишняя секция или ключ SHALL приводить к fail-fast ошибке с детерминированным путем ключа в diagnostics.

#### Scenario: Обнаружена неизвестная секция
- **WHEN** в `.apidev/config.toml` присутствует секция вне набора `paths`, `inputs`, `generator`, `evolution`, `openapi`
- **THEN** загрузка завершается fail-fast ошибкой до выполнения команд `validate`, `diff`, `gen`, `init`
- **AND** diagnostics содержит детерминированный `key_path` для неизвестной секции

#### Scenario: Обнаружен неизвестный ключ в известной секции
- **WHEN** в известной секции указан ключ, не объявленный в нормативном наборе
- **THEN** загрузка завершается fail-fast ошибкой до выполнения бизнес-операций
- **AND** diagnostics содержит детерминированный `key_path` для неизвестного ключа

### Requirement: Детерминированное разрешение путей конфигурации
Система SHALL разрешать относительные пути из `.apidev/config.toml` относительно `project_dir`, выполнять нормализацию пути до boundary-check и запрещать выход за пределы `project_dir`.

#### Scenario: Разрешение относительного пути внутри проекта
- **WHEN** путь в конфиге задан относительно (включая `evolution.release_state_file`)
- **THEN** система разрешает путь относительно `project_dir`
- **AND** использует нормализованный путь для последующих операций

#### Scenario: Попытка выхода за пределы `project_dir`
- **WHEN** после нормализации путь указывает за пределы `project_dir`
- **THEN** загрузка завершается fail-fast ошибкой валидации
- **AND** diagnostics детерминированно включает поля `key_path`, `resolved_path`, `project_dir`, `error_code`
