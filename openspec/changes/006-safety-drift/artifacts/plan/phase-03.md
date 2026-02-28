# Phase 03 - Verification and Documentation Sync

## Цель
Закрыть verification и документационную консистентность для remove-scenarios в CLI/testing contracts.

## Шаги
1. Обновить `docs/reference/cli-contract.md` по drift/exit матрице для `REMOVE`.
2. Обновить `docs/process/testing-strategy.md` checklist remove-case.
3. Добавить regression-тесты для remove-only и remove-conflict сценариев.
4. Выполнить full verification и strict OpenSpec validation.

## Выходы
- Синхронизированные reference/process документы.
- Полный regression-набор unit/contract/integration тестов.
- Готовность change к implement acceptance.

## Риски и rollback
- Риск: противоречия между документацией и фактическим поведением CLI.
- Rollback: блокировка merge до устранения расхождений.

## Quality Gate
- Тестовый набор и docs-check проходят стабильно.
- `openspec validate 006-safety-drift --strict --no-interactive` завершен успешно.
