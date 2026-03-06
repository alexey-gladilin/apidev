# Phase 03 - Formal Deprecation Policy

## Цель
Зафиксировать lifecycle deprecation и правила перехода к удалению в governance-модели этапа D.

## Scope
- definition lifecycle состояний и переходов;
- grace period и breaking classification rules;
- отражение deprecation статуса в CLI/docs/generated metadata.

## Outputs
- `artifacts/design/02-behavior.md`
- `artifacts/design/03-decisions.md`
- `artifacts/design/04-testing.md`
- `tasks.md` (Phase 03 items)

## Verification
- Scenario review против `specs/contract-evolution-integration/spec.md`.
- Согласованность с compatibility taxonomy.

## Definition of Done
- lifecycle и transitions формализованы;
- удаление без deprecation window помечено как breaking;
- правила публикации статуса в CLI/docs определены.
