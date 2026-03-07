# Возможности apidev CLI (снимок на 2026-03-07)

Источник: локальные `--help`/`--version` команды в этом репозитории.

## Метаданные снимка

- `snapshot_version`: `0.2.2`
- `captured_at`: `2026-03-07`

## Как поддерживать актуальность

- Предпочитать авто-обновление этого файла по результатам `--help`, а не ручные правки.
- Перед использованием capabilities проверять `apidev --version`.
- Если `detected_version != snapshot_version`, считать этот файл устаревшим и переснимать snapshot.
- Минимальный набор команд для пересъема:
  - `apidev --version`
  - `apidev --help`
  - `apidev init --help`
  - `apidev validate --help`
  - `apidev graph --help`
  - `apidev diff --help`
  - `apidev gen --help`
  - `apidev version --help`
- После обновления help-снимка менять `snapshot_version` и `captured_at`.

## Корневой уровень

Команда: `apidev --help`

Глобальные опции:

- `--version` / `-v`
- `--install-completion`
- `--show-completion`
- `--help` / `-h`

Подкоманды:

- `init` — инициализировать директорию проекта apidev.
- `validate` — валидировать контракты и правила.
- `graph` — исследовать граф зависимостей контрактов.
- `diff` — показать предпросмотр изменений генерируемых файлов.
- `gen` — сгенерировать код из контрактов.
- `version` — вывести версию приложения.

## `version`

Команда: `apidev version --help`

Флаги:

- `--help` / `-h`

## `init`

Команда: `apidev init --help`

Флаги:

- `--project-dir PATH` (по умолчанию `.`)
- `--repair`
- `--force`
- `--runtime [fastapi|none]` (по умолчанию `fastapi`)
- `--integration-mode [off|scaffold|full]` (по умолчанию `scaffold`)
- `--integration-dir TEXT` (по умолчанию `.apidev/output/integration`)

## `validate`

Команда: `apidev validate --help`

Флаги:

- `--project-dir PATH` (по умолчанию `.`)
- `--json`

## `graph`

Команда: `apidev graph --help`

Флаги:

- `--project-dir PATH` (по умолчанию `.`)
- `--format [text|json|mermaid]` (по умолчанию `text`)

## `diff`

Команда: `apidev diff --help`

Флаги:

- `--project-dir PATH` (по умолчанию `.`)
- `--json`
- `--scaffold`
- `--no-scaffold`
- `--compatibility-policy TEXT` (`warn`/`strict`)
- `--baseline-ref TEXT`

## `gen`

Команда: `apidev gen --help`

Флаги:

- `--project-dir PATH` (по умолчанию `.`)
- `--check / --no-check`
- `--json`
- `--scaffold`
- `--no-scaffold`
- `--compatibility-policy TEXT` (`warn`/`strict`)
- `--baseline-ref TEXT`
- `--include-endpoint TEXT` (повторяемый)
- `--exclude-endpoint TEXT` (повторяемый)

## Ограничения исполнения

- Базовый способ запуска: прямой вызов `apidev ...`.
- Fallback при `command not found`: `uv run apidev ...`.
- `--scaffold` и `--no-scaffold` взаимоисключающие.
- `init --repair` и `init --force` взаимоисключающие.
- `init --runtime none` нельзя комбинировать с `--integration-mode full`.
- `--integration-dir` должен быть относительным путём внутри `project_dir`.
- Для анализа графа зависимостей предпочтителен `graph --format json`; `graph --format mermaid` подходит для визуализации.
- Для JSON-ориентированного анализа в LLM предпочтителен запуск с `--json`.
- Для операций записи в файлы (`gen`, `init --force`) использовать подтверждение пользователя.
