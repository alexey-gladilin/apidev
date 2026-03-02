## Контекст
`apidev` находится в стадии `Foundation Complete -> Productization Execution`; в roadmap обозначен Horizon 2 (Release Automation). При этом в репозитории отсутствуют `.github/workflows` для release-билда бинарников и отсутствует release/distribution surface в `README`.

## Цели / Не-цели
- Цели:
  - зафиксировать целевую архитектуру release pipeline для `apidev` по аналогии с `dbspec`;
  - определить deterministic release artifacts contract и quality gates;
  - определить process surface (README + release checklist docs).
- Не-цели:
  - реализация production-кода в proposal-фазе;
  - изменение runtime-бизнес-логики validate/diff/gen pipeline.

## Решения
- Использовать GitHub Actions release workflow с matrix build по `macOS|Windows|Linux`.
- Ввести обязательный smoke gate перед upload release assets.
- Зафиксировать deterministic artifact naming и release trigger contract.
- Выделить Homebrew publish path в отдельную gated job.

## Риски / Компромиссы
- Риск: platform-specific differences сборки бинарника между ОС.
  - Митигация: отдельные smoke checks и artifact packaging per OS.
- Риск: ошибки публикации Homebrew formula из-за секретов/прав доступа.
  - Митигация: отдельный fail-fast pre-check секрета и изолированный publish job.

## Linked Artifacts
- Research: [artifacts/research/2026-03-02-release-automation-baseline.md](./artifacts/research/2026-03-02-release-automation-baseline.md)
- Design package index: [artifacts/design/README.md](./artifacts/design/README.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/release-automation/spec.md](./specs/release-automation/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды.
