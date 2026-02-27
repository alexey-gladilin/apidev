# Phase 01 - Compatibility Classification Contract

## Цель
Зафиксировать taxonomy и контракты поведения для классификации изменений в `diff`/`gen --check`.

## Scope
- определить структуры classification результата;
- определить mapping в diagnostics и exit behavior;
- определить extension points в core/application слоях.

## Outputs
- `artifacts/design/02-behavior.md`
- `artifacts/design/03-decisions.md`
- `tasks.md` (Phase 01 items)

## Verification
- Traceability review против `specs/contract-evolution-integration/spec.md`.
- Проверка согласованности с `docs/reference/cli-contract.md`.

## Definition of Done
- категории совместимости формально определены;
- CLI behavior для `diff` и `gen --check` описан без противоречий;
- extension points не нарушают архитектурные границы.
