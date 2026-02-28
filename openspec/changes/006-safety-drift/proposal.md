# Change: Horizon 1 - Safety/Drift Completion (REMOVE governance)

## Почему
В `docs/roadmap.md` для Horizon 1 зафиксирован критичный gap: в generation-пайплайне отсутствует полноценный `REMOVE`, из-за чего дрейф stale generated artifacts не покрыт единым детерминированным контрактом `diff` и `gen --check`.

## Что изменится
- Добавляется capability `safety-drift` с нормативными требованиями для удаления stale generated artifacts.
- Формализуется `REMOVE` как разрешенный тип change-плана с write-boundary ограничениями.
- Синхронизируется drift-поведение и exit semantics для сценариев удаления в `apidev diff` и `apidev gen --check`.
- Фиксируются обязательные diagnostics и verification-сценарии для remove/conflict кейсов.

## Влияние
- Затронутые спеки: `safety-drift` (новая capability в этом change-пакете).
- Затронутый код (target для implement-фазы):
  - `src/apidev/application/dto/generation_plan.py`
  - `src/apidev/application/services/diff_service.py`
  - `src/apidev/application/services/generate_service.py`
  - `src/apidev/commands/diff_cmd.py`
  - `src/apidev/commands/generate_cmd.py`
  - `src/apidev/infrastructure/output/writer.py`
  - `tests/unit/**`, `tests/contract/**`, `tests/integration/**`
  - `docs/reference/cli-contract.md`, `docs/process/testing-strategy.md`
- Breaking: на proposal-этапе нет runtime-breaking изменений; пакет описывает проектирование и план implement-фазы.

## Linked Artifacts
- Research baseline: [artifacts/research/2026-02-28-safety-drift-remove-baseline.md](./artifacts/research/2026-02-28-safety-drift-remove-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/safety-drift/spec.md](./specs/safety-drift/spec.md)

## Границы этапа
Этот change-пакет покрывает Proposal/Design/Plan и readiness к implement.
Implementation выполняется отдельно через `/openspec-implement` или `/openspec-implement-single` после review/approval.
