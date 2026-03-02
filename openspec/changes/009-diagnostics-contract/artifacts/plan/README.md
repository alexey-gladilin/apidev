# Plan Package: 009-diagnostics-contract

## Цель
Разбить implement-фазу на проверяемые этапы для унификации machine-readable diagnostics contract в `validate`, `diff`, `gen --check`, `gen`.

## Фазы
- [phase-01.md](./phase-01.md) - unified diagnostics model и CLI JSON surface.
- [phase-02.md](./phase-02.md) - compatibility/drift reporting alignment и deterministic output.
- [phase-03.md](./phase-03.md) - docs/tests sync и финальная strict validation.
- [implementation-handoff.md](./implementation-handoff.md) - handoff для `/openspec-implement`.

## Связи
- Tasks tracker: [../../tasks.md](../../tasks.md)
- Design package: [../design/README.md](../design/README.md)
