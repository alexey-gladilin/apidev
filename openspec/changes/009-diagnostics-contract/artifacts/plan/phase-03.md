# Phase 03: Docs, Tests, and Validation Sync

## Цель
Синхронизировать нормативную документацию и тестовые контракты с новым diagnostics contract.

## Scope
- Обновление `docs/reference/cli-contract.md` и `docs/process/testing-strategy.md`.
- Добавление regression tests для unified envelope/codes/exit semantics.
- Финальная strict валидация OpenSpec change.

## Deliverables
- Обновленные reference/process docs.
- Unit+integration regression tests.
- Strict validation report.

## Verification
- `make docs-check`
- `uv run pytest tests/unit tests/integration`
- `openspec validate 009-diagnostics-contract --strict --no-interactive`

## Exit Criteria
- Документация и тесты отражают единый diagnostics contract.
- Change-пакет проходит strict validation и готов к implement phase.
