# Phase 02 - Optional DBSpec Integration Contract

## Цель
Определить контракт optional read-only интеграции `dbspec` без разрушения standalone сценариев APIDev.

## Scope
- формат и границы использования dbspec hints;
- fallback behavior при отсутствии/ошибке доступа к hints;
- deterministic merge policy между контрактом и hints.

## Outputs
- `artifacts/design/01-architecture.md`
- `artifacts/design/02-behavior.md`
- `artifacts/design/03-decisions.md`
- `tasks.md` (Phase 02 items)

## Verification
- Согласованность с `docs/product/vision.md` (optional + read-only).
- Проверка на соответствие deterministic generation инвариантам.

## Definition of Done
- интеграция описана как read-only и optional;
- fallback не блокирует validate/diff/gen;
- merge policy обеспечивает стабильный результат.
