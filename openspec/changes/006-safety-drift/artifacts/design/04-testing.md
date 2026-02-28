# Тестовая стратегия: REMOVE safety/drift

## Цель
Подтвердить, что `REMOVE` корректно участвует в preview/check/apply режимах без нарушения write-boundary и с детерминированным drift-signal.

## Unit tests
- Планирование `REMOVE` в `DiffService` для stale generated artifacts.
- Отсутствие `REMOVE` при полном совпадении expected и фактического generated набора.
- Deterministic ordering `REMOVE` по пути.
- Diagnostic codes для remove-conflict и boundary-violation.

## Contract tests
- Boundary policy: `REMOVE` за пределами generated root отклоняется.
- Read-only policy: `diff` и `gen --check` не удаляют файлы.
- Drift contract: remove-only план => `drift` для `diff`/`check`.

## Integration tests
- Roundtrip: generate -> удалить контракт -> `diff` показывает `REMOVE` -> `gen --check` возвращает drift -> `gen` удаляет stale artifacts -> повторный `gen --check` возвращает no-drift.
- Conflict: stale файл удален вручную перед apply -> ожидаемый `error` diagnostic.
- Mixed-plan: одновременно `ADD/UPDATE/REMOVE` в одном запуске и стабильный итог.

## Документационные проверки
- `docs/reference/cli-contract.md`: матрица drift/exit обновлена для remove-case.
- `docs/process/testing-strategy.md`: verification checklist содержит remove-сценарии.

## Quality gates
- `uv run pytest tests/unit tests/contract tests/integration -k "remove or drift or writer"`
- `uv run pytest tests/integration/test_generate_roundtrip.py`
- `uv run pytest tests/unit/test_cli_conventions.py`
