# Phase 03 — JSON Output & CLI Contract

## Scope
- Формализовать JSON payload для `apidev validate --json`.
- Зафиксировать консистентность между human и JSON режимами.
- Зафиксировать exit-code policy на success/failure.

## Deliverables
- JSON diagnostics contract (diagnostics array + summary).
- Правила рендеринга human/json из единого diagnostics источника.
- Integration/contract тест-план для `--json` (success/failure).

## Verification
- `pytest tests/integration -k validate`
- `pytest tests/unit -k validate_cmd`
- `ruff check src tests`
- JSON parseability checks for CLI output

## Definition of Done
- JSON контракт вывода стабилен и пригоден для CI-парсинга.
- Default human UX не ломается без `--json`.
- Exit code consistently: `0` без ошибок, `1` при `severity=error`.
