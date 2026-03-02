# Change: Автоматическое управление release-state в `apidev gen`

## Почему
Сейчас `release-state` используется как источник `release_number` и `baseline_ref` для compatibility/deprecation checks, но не создается автоматически и не синхронизируется при `apidev gen`. Это приводит к диагностике `release-state-invalid` и `baseline-missing` в ситуациях, где пользователь ожидает bootstrap по умолчанию.

## Что изменится
- Модифицируется capability `contract-evolution-integration`:
  - `apidev gen` (apply mode) автоматически создает `release-state`, если файл отсутствует.
  - `apidev gen` (apply mode) автоматически обновляет `release_number` при фактически примененных генератором изменениях.
  - `apidev gen` (apply mode) синхронизирует `baseline_ref` по policy precedence (`CLI -> release-state -> git fallback`).
- Фиксируется поведение в no-git/no-baseline сценариях:
  - детерминированные diagnostics;
  - отсутствие скрытых write в read-only режимах.
- Контракты документации и тестирования синхронизируются с новой семантикой release-state lifecycle.

## Влияние
- Затронутые спеки: `contract-evolution-integration` (MODIFIED).
- Затронутый код (target implement-фазы):
  - `src/apidev/application/services/generate_service.py`
  - `src/apidev/application/services/diff_service.py`
  - `src/apidev/infrastructure/config/toml_loader.py` (при необходимости расширения read/write контракта)
  - `tests/unit/**`, `tests/integration/**`
  - `docs/reference/contract-format.md`
  - `docs/reference/cli-contract.md`
- Breaking: нет, изменение направлено на автоматизацию и снижение ручных шагов.

## Linked Artifacts
- Research: [artifacts/research/2026-03-02-release-state-baseline.md](./artifacts/research/2026-03-02-release-state-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/contract-evolution-integration/spec.md](./specs/contract-evolution-integration/spec.md)

## Границы этапа
Этот change-пакет покрывает Proposal/Design/Plan и readiness к implement.
Implementation выполняется отдельно через `/openspec-implement` или `/openspec-implement-single` после review/approval.
