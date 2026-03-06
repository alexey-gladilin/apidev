# Phase 01 — Validate-First Pipeline & Drift Preview Governance

## Цель
Зафиксировать implement-план для обязательной последовательности `validate -> diff/check` и немутирующего preview-контура.

## Планируемые шаги
1. Уточнить preflight validation contract для `apidev diff` и `apidev gen` с единым failure-signal.
2. Зафиксировать read-only semantics для `diff` и `gen --check` без filesystem writes.
3. Согласовать drift-status semantics (drift/no-drift/error) для CI gate и CLI-отчета.

## Выходы
- Фазовый план `REQ-1/REQ-2`: `artifacts/plan/phase-01.md`
- Поведенческие уточнения режимов: `artifacts/design/02-behavior.md`
- Решения по сигналам завершения: `artifacts/design/03-decisions.md`

## Quality Gate
- Документирован validate-first блокирующий сценарий для невалидного входа.
- Зафиксировано доказуемое non-mutation поведение `diff` и `gen --check`.
- Drift-status трактуется консистентно между сервисным и CLI уровнями.
