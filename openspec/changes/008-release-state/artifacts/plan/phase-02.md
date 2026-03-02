# Phase 02 - CLI/Diagnostics Integration

## Scope
- Согласовать write behavior с текущим CLI flow (`gen`, `gen --check`, `diff`).
- Гарантировать, что diagnostics baseline/release-state остаются детерминированными.
- Зафиксировать поведение для no-git/invalid-baseline сценариев.

## Outputs
- `src/apidev/commands/generate_cmd.py` (при необходимости сообщений/гейтов)
- `src/apidev/application/services/diff_service.py` (только если нужна синхронизация semantics)
- `tests/integration/test_compatibility_policy_cli.py`

## Verification
- `uv run pytest tests/integration/test_compatibility_policy_cli.py`

## Definition of Done
- `diff` и `gen --check` остаются read-only.
- `gen apply` sync release-state не ломает exit semantics.
- no-git/invalid baseline сценарии остаются явно диагностируемыми.
