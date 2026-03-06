# Implementation Handoff: 002-transport-generation

## Порядок выполнения
1. Выполнить Phase 01: контрактный baseline generation surface, registry, bridge.
2. Выполнить Phase 02: внедрение template architecture и safety guardrails.
3. Выполнить Phase 03: тестовая матрица, интеграционные проверки и финальная валидация.
4. После завершения generation implement-фазы актуализировать `docs/roadmap.md` по статусу Stage B и фактически доставленному scope.

## Зависимости
- `P2` стартует после фиксации контрактов `P1`.
- `P3` стартует после завершения template/safety решений `P2`.
- Финальный merge допустим только после прохождения тестового минимума из `artifacts/design/04-testing.md`.

## Scope implement-фазы
- Включено: эволюция generation pipeline и templates для transport MVP+.
- Исключено: breaking-aware modes этапа C, repository/business code generation.

## Команда запуска
Implement выполняется отдельной командой: `/openspec-implement 002-transport-generation` (или `/openspec-implement-single 002-transport-generation`).
