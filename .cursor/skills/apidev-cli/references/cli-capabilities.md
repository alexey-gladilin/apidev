# Возможности apidev CLI (снимок на 2026-03-04)

Источник: локальные `--help` команды в этом репозитории.

## Как поддерживать актуальность

- Предпочитать авто-обновление этого файла по результатам `--help`, а не ручные правки.
- Минимальный набор команд для пересъема:
  - `apidev --help`
  - `apidev init --help`
  - `apidev validate --help`
  - `apidev diff --help`
  - `apidev gen --help`
- После обновления help-снимка менять дату в заголовке файла.

## Корневой уровень

Команда: `apidev --help`

Глобальные опции:

- `--install-completion`
- `--show-completion`
- `--help` / `-h`

Подкоманды:

- `init` — инициализировать директорию проекта apidev.
- `validate` — валидировать контракты и правила.
- `diff` — показать предпросмотр изменений генерируемых файлов.
- `gen` — сгенерировать код из контрактов.

## `init`

Команда: `apidev init --help`

Флаги:

- `--project-dir PATH` (по умолчанию `.`)
- `--repair`
- `--force`
- `--runtime [fastapi|none]` (по умолчанию `fastapi`)
- `--integration-mode [off|scaffold|full]` (по умолчанию `scaffold`)
- `--integration-dir TEXT` (по умолчанию `integration`)

## `validate`

Команда: `apidev validate --help`

Флаги:

- `--project-dir PATH` (по умолчанию `.`)
- `--json`

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
- Для JSON-ориентированного анализа в LLM предпочтителен запуск с `--json`.
- Для операций записи в файлы (`gen`, `init --force`) использовать подтверждение пользователя.
