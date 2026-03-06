# Implementation Handoff: 010-release-automation

## Входные артефакты
- Proposal: [../../proposal.md](../../proposal.md)
- Design: [../../design.md](../../design.md)
- Tasks: [../../tasks.md](../../tasks.md)
- Spec delta: [../../specs/release-automation/spec.md](../../specs/release-automation/spec.md)
- Research: [../research/2026-03-02-release-automation-baseline.md](../research/2026-03-02-release-automation-baseline.md)
- Design package: [../design/README.md](../design/README.md)
- Plan package: [./README.md](./README.md)

## Порядок реализации
1. `Phase 01` — workflow skeleton, matrix build/smoke/package/publish.
2. `Phase 02` — release docs surface + optional Homebrew gated path.
3. `Phase 03` — regression/governance hardening + strict validation.

## Межфазные зависимости
- `Phase 02` стартует только после стабилизации release contract из `Phase 01`.
- `Phase 03` стартует только после синхронизации workflow и docs из `Phase 01-02`.
- Любая смена artifact naming contract требует обратного обновления docs и tests до завершения `Phase 03`.

## Реализационные принципы
- Не менять runtime-функциональность CLI; фокус только на release automation/process surface.
- Публикация assets разрешена только после успешного smoke gate во всех обязательных matrix ветках.
- Homebrew path должен быть изолирован и secret-gated, без влияния на консистентность core release assets.

## Traceability (Spec -> Plan -> Tasks)
- `Release trigger starts multi-OS build` -> `Phase 01` (`tasks.md`: 1.1).
- `Binary smoke checks gate artifact publication` -> `Phase 01` (`tasks.md`: 1.2).
- `Release assets are published deterministically` -> `Phase 01` (`tasks.md`: 1.3).
- `Distribution surface is documented` -> `Phase 02` (`tasks.md`: 2.2).
- `Release checklist is explicit and test-backed` -> `Phase 02` (`tasks.md`: 2.1) + `Phase 03` (`tasks.md`: 3.1).
- `Homebrew publish is secret-gated` -> `Phase 02` (`tasks.md`: 2.3).

## Files Updated In This Planning Iteration
- `openspec/changes/010-release-automation/artifacts/plan/README.md`
- `openspec/changes/010-release-automation/artifacts/plan/phase-01.md`
- `openspec/changes/010-release-automation/artifacts/plan/phase-02.md`
- `openspec/changes/010-release-automation/artifacts/plan/phase-03.md`
- `openspec/changes/010-release-automation/artifacts/plan/implementation-handoff.md`
- `openspec/changes/010-release-automation/tasks.md`

## Definition of Done (Implement Handoff)
- Плановые артефакты и `tasks.md` синхронизированы по scope, verification и DoD.
- Все задачи в planning stage (`[ ]`), без статусов implement/blocked/rejected.
- Есть явная трассируемость от spec scenarios к implement-фазам и задачам.
