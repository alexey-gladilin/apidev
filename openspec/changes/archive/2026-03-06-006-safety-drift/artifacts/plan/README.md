# Plan Artifact Package: 006-safety-drift

## Цель
Разбить implement-фазу Horizon 1 Safety/Drift Completion на последовательные этапы с явными quality gates для `REMOVE`.

## Связанные core-файлы
- Proposal: [../../proposal.md](../../proposal.md)
- Design summary: [../../design.md](../../design.md)
- Spec delta: [../../specs/safety-drift/spec.md](../../specs/safety-drift/spec.md)
- Tasks tracker: [../../tasks.md](../../tasks.md)

## Этапы
- [phase-01.md](./phase-01.md) - REMOVE planning contract и drift preview alignment
- [phase-02.md](./phase-02.md) - Apply semantics, boundary safety и diagnostics
- [phase-03.md](./phase-03.md) - Verification matrix, docs sync и readiness
- [implementation-handoff.md](./implementation-handoff.md) - handoff в implement-команду

## Трассировка на spec delta
- `REQ-1` -> `phase-01`
- `REQ-2` -> `phase-01`, `phase-03`
- `REQ-3` -> `phase-02`, `phase-03`
- `REQ-4` -> `phase-02`, `phase-03`

## Правило исполнения
`tasks.md` остается planning-only и single-writer: обновление статусов выполнения производится только в отдельной implement-фазе.
