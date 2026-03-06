# Phase 02 — Write Boundary Enforcement & Deterministic Planning

## Цель
Подготовить implement-план для жесткого write-boundary и детерминированного diff-планирования.

## Планируемые шаги
1. Зафиксировать policy записи только в `generated-root` и обработку boundary violations.
2. Уточнить запрет на трактовку `generated-root` как файла и требования к отказоустойчивости apply.
3. Определить deterministic ordering/normalization для стабильного diff-плана и повторяемого drift-signal.

## Выходы
- Фазовый план `REQ-3/REQ-4`: `artifacts/plan/phase-02.md`
- Архитектурная трассировка boundary/determinism: `artifacts/design/01-architecture.md`
- Decision log по safety trade-offs: `artifacts/design/03-decisions.md`

## Quality Gate
- Write-path вне `generated-root` формально запрещен как contract.
- Зафиксирована стратегия deterministic ordering для эквивалентных входов.
- Определены acceptance-критерии idempotent apply (`gen` повторно без новых изменений).
