# Change: Horizon 2 — Release Automation (multi-OS binary pipeline)

## Почему
В `apidev` требуется завершить и стандартизировать репозиторный release-процесс для публикации standalone binary артефактов под `macOS`, `Windows`, `Linux`. Часть базового контура уже реализована, но отсутствует полный process/documentation/security contract для production-ready публикации.

Исследование baseline показало, что в `dbspec` уже реализован работающий GitHub release-поток с matrix build/smoke/package/release assets и Homebrew publish. Для `apidev` этот change фиксирует переход от частично реализованного baseline к целевому release contract Horizon 2.

## Что изменится
- Добавляется capability `release-automation`:
  - GitHub workflow для сборки бинарников `apidev` на `macOS`, `Windows`, `Linux`;
  - release-триггер на `release: published` и ручной `workflow_dispatch`;
  - smoke-проверка собранных бинарников перед публикацией;
  - упаковка и публикация артефактов в GitHub Releases (и как workflow artifacts);
  - опциональный publish Homebrew formula (macOS path) с контролируемым секретом и отдельной job.
- Формализуется release documentation:
  - distribution section в `README.md`;
  - release process/checklist в `docs/process/*`.
- Формализуются quality gates release pipeline:
  - обязательные команды верификации перед upload/publish;
  - deterministic naming/versioning артефактов.

## Влияние
- Затронутые спеки: `release-automation` (ADDED).
- Затронутый код и процессы (target implement-фазы):
  - `.github/workflows/*` (новые release workflow)
  - `scripts/*` (build/smoke/package helpers при необходимости)
  - `Makefile` (build/package/smoke targets)
  - `README.md`
  - `docs/process/*` (release flow/checklist)
- Breaking:
  - для runtime CLI-контракта — нет;
  - для CI/release process — новый обязательный контур публикации.

## Linked Artifacts
- Research: [artifacts/research/2026-03-02-release-automation-baseline.md](./artifacts/research/2026-03-02-release-automation-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/release-automation/spec.md](./specs/release-automation/spec.md)

## Границы этапа
Этот change-пакет используется как execution tracker для поэтапной реализации Horizon 2.
Phase 01 уже завершена в рамках этого change, а оставшиеся задачи выполняются через `/openspec-implement` или `/openspec-implement-single` до полного закрытия Phase 02-03.
