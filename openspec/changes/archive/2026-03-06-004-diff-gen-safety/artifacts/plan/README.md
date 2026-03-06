# Plan Artifact Package: 004-diff-gen-safety

## Цель
Разбить implement-фазу Stage C на управляемые этапы `P1 -> P2 -> P3` с явными quality gates для safety-контура `validate -> diff -> gen`.

## Связанные core-файлы
- Proposal: [../../proposal.md](../../proposal.md)
- Design summary: [../../design.md](../../design.md)
- Spec delta: [../../specs/diff-gen-safety/spec.md](../../specs/diff-gen-safety/spec.md)
- Tasks tracker: [../../tasks.md](../../tasks.md)

## Этапы
- [phase-01.md](./phase-01.md) — Validate-First Pipeline & Drift Preview Governance (`REQ-1`, `REQ-2`)
- [phase-02.md](./phase-02.md) — Write Boundary Enforcement & Deterministic Planning (`REQ-3`, `REQ-4`)
- [phase-03.md](./phase-03.md) — Verification Matrix, CLI Contract Sync & Readiness (`REQ-1..REQ-4`)
- [implementation-handoff.md](./implementation-handoff.md) — сквозной handoff в implement-команду

## Трассировка на spec delta
- `REQ-1` Validate-First Safety Pipeline -> `phase-01`, `phase-03`
- `REQ-2` Drift Governance Modes -> `phase-01`, `phase-03`
- `REQ-3` Generated Write Boundary Safety -> `phase-02`, `phase-03`
- `REQ-4` Deterministic Drift Signal -> `phase-02`, `phase-03`

## Правило исполнения
`tasks.md` остается single-writer tracker: orchestrator фиксирует planning-готовность, implement-команда выполняет кодовые изменения в отдельной фазе.
