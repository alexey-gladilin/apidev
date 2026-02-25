# Change: apidev CLI Tool Architecture and Skeleton

## Why
Требуется спроектировать архитектуру самого `apidev` как бинарного CLI-инструмента, который запускается в чужих проектах и генерирует API-код в их рабочем дереве.
Без фиксированной архитектуры CLI возрастает риск хаотичного роста команд, связности модулей и небезопасной генерации файлов.

## What Changes
- Добавляется capability `cli-tool-architecture` с требованиями к структуре исходников `apidev`.
- Фиксируется модульная архитектура инструмента: `cli` -> `commands` -> `application` -> `core` -> `infrastructure`.
- Фиксируется минимальный набор CLI-команд MVP: `init`, `validate`, `diff`, `generate`.
- Фиксируется packaging-модель бинарника через Python entrypoint (`apidev`).
- Фиксируются зависимости и правила безопасной генерации в целевом проекте (write only generated zone, dry-run/diff/check).

## Impact
- Affected specs: `cli-tool-architecture` (new)
- Affected code: `pyproject.toml`, `src/apidev/**`, `tests/**`, стартовые шаблоны генератора
- Breaking: нет (новая capability)
