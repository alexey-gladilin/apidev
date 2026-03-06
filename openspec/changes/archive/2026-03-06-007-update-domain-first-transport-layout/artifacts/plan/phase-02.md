# Phase 02 - Template & Runtime Wiring Update

## Цель
Применить новый layout в шаблонах и runtime wiring.

## Scope
- template updates (router/schema/operation_map imports);
- integration regression для compile + no-drift.

## Exit Criteria
- `apidev gen` формирует только domain-first output;
- повторный `apidev gen --check` возвращает `no-drift`.
