# Plan Package: 010-release-automation

## Цель
Подготовить implement-ready план для автоматизации релизов standalone binary `apidev` под `macOS`, `Windows`, `Linux` с проверяемыми фазами и явными quality gates.

## Фазы
- [phase-01.md](./phase-01.md) - каркас release workflow, multi-OS matrix, build/smoke/package/publish contract.
- [phase-02.md](./phase-02.md) - release publishing surface в документации и optional Homebrew path.
- [phase-03.md](./phase-03.md) - надежность, governance, regression guards и strict validation.
- [implementation-handoff.md](./implementation-handoff.md) - implement handoff и traceability.

## Зависимости фаз
- `Phase 01 -> Phase 02 -> Phase 03`.
- `Phase 02` опирается на workflow contract из `Phase 01`.
- `Phase 03` опирается на реализованные pipeline/docs артефакты из `Phase 01` и `Phase 02`.

## Связи
- Tasks tracker: [../../tasks.md](../../tasks.md)
- Proposal: [../../proposal.md](../../proposal.md)
- Design: [../../design.md](../../design.md)
- Design package: [../design/README.md](../design/README.md)
- Spec delta: [../../specs/release-automation/spec.md](../../specs/release-automation/spec.md)
