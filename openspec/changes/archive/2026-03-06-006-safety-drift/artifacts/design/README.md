# Design Artifact Package: 006-safety-drift

## Контекст
Пакет описывает проектирование завершения Horizon 1 Safety/Drift: добавление полноценного `REMOVE` в generation plan с консистентной drift-семантикой и сохранением write-boundary.

## Входы
- Proposal: `openspec/changes/006-safety-drift/proposal.md`
- Design summary: `openspec/changes/006-safety-drift/design.md`
- Spec delta: `openspec/changes/006-safety-drift/specs/safety-drift/spec.md`
- Research baseline: `openspec/changes/006-safety-drift/artifacts/research/2026-02-28-safety-drift-remove-baseline.md`

## Состав пакета
- [01-architecture.md](./01-architecture.md)
- [02-behavior.md](./02-behavior.md)
- [03-decisions.md](./03-decisions.md)
- [04-testing.md](./04-testing.md)

## Трассировка на spec delta
- `REQ-1` REMOVE операция в generation plan -> `01-architecture`, `02-behavior`, `03-decisions`
- `REQ-2` Drift семантика удаления для diff и gen --check -> `02-behavior`, `03-decisions`, `04-testing`
- `REQ-3` Apply semantics для REMOVE в apidev gen -> `01-architecture`, `02-behavior`, `04-testing`
- `REQ-4` Deterministic ordering и diagnostics для REMOVE -> `02-behavior`, `03-decisions`, `04-testing`

## Assumptions
- Ownership boundary (`generated` vs `manual`) не меняется.
- `diff` и `gen --check` остаются read-only режимами.
- CLI drift-status остается каноническим (`drift|no-drift|error`).

## Unresolved Questions
- Нужен ли отдельный diagnostic code для "artifact already absent at apply time".
- Нужно ли расширять writer-порт отдельным delete API или реализовать это на слое сервиса.
