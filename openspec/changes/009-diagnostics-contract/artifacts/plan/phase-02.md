# Phase 02: Compatibility and Drift Reporting Alignment

## Цель
Выровнять compatibility/drift diagnostics под единый контракт без изменения существующей policy-семантики.

## Scope
- Нормализация compatibility diagnostics в общем envelope.
- Детерминированный порядок diagnostics и стабильные summary counters.
- Backward-safe сохранение plain-text UX.

## Deliverables
- Обновленный compatibility printer/serializer слой.
- Обновленные integration tests для `warn|strict` и drift scenarios.

## Verification
- `uv run pytest tests/integration/test_compatibility_policy_cli.py`
- `uv run pytest tests/unit -k "deterministic and diagnostics"`

## Exit Criteria
- `warn|strict` behavior и policy gate работают без регрессий.
- JSON output детерминирован и консистентен между повторными запусками.
