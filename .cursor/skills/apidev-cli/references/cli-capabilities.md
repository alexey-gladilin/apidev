# Возможности apidev CLI (снимок на 2026-03-03)

Источник: локальные `--help` команды в этом репозитории.

## Корневой уровень

Команда: `apidev --help`

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
- Для JSON-ориентированного анализа в LLM предпочтителен запуск с `--json`.
- Для операций записи в файлы (`gen`, `init --force`) использовать подтверждение пользователя.
