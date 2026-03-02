# Testing Strategy

## Цель
Подтвердить корректный lifecycle release-state для `gen apply` и отсутствие side effects в read-only режимах.

## Unit
- Проверка create payload для отсутствующего release-state.
- Проверка bump/no-bump `release_number` в зависимости от наличия applied changes.
- Проверка baseline precedence (`CLI`, `release-state`, fallback).
- Проверка корректной обработки invalid/missing release-state.

## Integration
- `gen` создает release-state при его отсутствии.
- `gen` увеличивает `release_number` при наличии изменений.
- `gen` не увеличивает `release_number` на no-op.
- `diff` и `gen --check` не меняют release-state (mtime/content guard).
- Поведение при no-git/invalid-baseline соответствует diagnostics.

## Regression
- Сохранить существующие compatibility diagnostics и strict policy semantics.
- Сохранить текущие exit-контракты `diff`/`gen`/`gen --check`.

## Quality Gates
- `uv run pytest tests/unit -k "generate_service and release_state"`
- `uv run pytest tests/integration/test_compatibility_policy_cli.py`
- `uv run pytest tests/integration -k "generate and release_state"`
- `openspec validate 008-release-state --strict --no-interactive`
