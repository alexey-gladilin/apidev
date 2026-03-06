# Behavior

## 1. Загрузка конфигурации
- Загрузка выполняется из `.apidev/config.toml`.
- Если файл отсутствует, применяется канонический default payload нового формата.

## 2. Нормативная структура
```toml
[paths]
templates_dir = ".apidev/templates"
release_state_file = ".apidev/release-state.json"

[inputs]
contracts_dir = ".apidev/contracts"
shared_models_dir = ".apidev/models"

[generator]
generated_dir = ".apidev/output/api"
postprocess = "auto"
scaffold = true
scaffold_dir = ".apidev/integration"
scaffold_write_policy = "create-missing"

[evolution]
compatibility_policy = "warn"
grace_period_releases = 2

[openapi]
include_extensions = true
```

## 3. Валидация структуры
- Разрешены только секции `paths`, `inputs`, `generator`, `evolution`, `openapi`.
- Поле `version` не допускается.
- Любой неизвестный/legacy-ключ приводит к fail-fast ошибке.

## 4. Валидация путей
- Пути разрешаются относительно `project_dir`.
- Выход за `project.root` запрещен.
- Диагностика должна быть детерминированной и machine-readable.

## 5. Runtime-поведение
- `validate`, `diff`, `gen`, `init` используют одинаково разрешенный конфиг.
- Различия поведения команд не должны изменять трактовку ключей конфига.
