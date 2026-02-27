# Change: Этап D - Contract Evolution & Integrations

## Почему
После завершения этапа B проекту нужен формальный переход к управляемой эволюции контрактов: классификация совместимости изменений, формальная deprecation policy и опциональная интеграция с `dbspec`.
Снимок в `docs/roadmap.md` (27 февраля 2026) фиксирует эти возможности как целевое состояние этапа D.

## Что изменится
- Добавляется capability `contract-evolution-integration` с нормативными требованиями для этапа D.
- Формализуется compatibility classification для `apidev diff` и `apidev gen --check` как основа breaking-aware governance.
- Формализуется optional read-only integration с `dbspec` для schema hints без обязательной зависимости.
- Формализуется deprecation policy (маркировка, переходный период, контроль удаления).
- Определяются артефакты планирования и quality gates для отдельной implement-фазы.

## Влияние
- Затронутые спеки: `contract-evolution-integration` (новая capability в delta).
- Затронутый код (target для implement-фазы):
  - `src/apidev/core/rules/compatibility.py`
  - `src/apidev/application/services/diff_service.py`
  - `src/apidev/application/services/generate_service.py`
  - `src/apidev/core/models/**`
  - `src/apidev/commands/diff_cmd.py`
  - `src/apidev/commands/generate_cmd.py`
  - `docs/reference/cli-contract.md`
  - `docs/reference/contract-format.md`
  - `tests/unit/**`, `tests/contract/**`, `tests/integration/**`
- Breaking: нет на proposal-этапе; change описывает проектирование governance-механизмов и миграционных правил.

## Linked Artifacts
- Research baseline: [artifacts/research/2026-02-27-contract-evolution-integration-baseline.md](./artifacts/research/2026-02-27-contract-evolution-integration-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Implementation blueprint: [artifacts/plan/phase-04-implementation.md](./artifacts/plan/phase-04-implementation.md)
- Spec delta: [specs/contract-evolution-integration/spec.md](./specs/contract-evolution-integration/spec.md)

## Границы этапа
Эта change-заявка покрывает Proposal/Design/Plan, включая детальный blueprint фазы реализации.
Implementation выполняется отдельно через `/openspec-implement` или `/openspec-implement-single` после review/approval.
