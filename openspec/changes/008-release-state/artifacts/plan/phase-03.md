# Phase 03 - Documentation and Verification Sync

## Scope
- Обновить reference docs по новому lifecycle release-state.
- Добавить/обновить regression tests на auto-create и version bump.
- Выполнить strict OpenSpec + test validation.

## Outputs
- `docs/reference/contract-format.md`
- `docs/reference/cli-contract.md`
- `tests/unit/**`, `tests/integration/**`
- `openspec/changes/008-release-state/**`

## Verification
- `uv run pytest tests/unit tests/integration`
- `openspec validate 008-release-state --strict --no-interactive`

## Definition of Done
- Документация и тесты соответствуют implement-логике.
- Change-пакет проходит strict validation и готов к implement handoff.
