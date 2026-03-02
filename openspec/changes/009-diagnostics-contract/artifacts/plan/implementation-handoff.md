# Implementation Handoff: 009-diagnostics-contract

## Входные артефакты
- Proposal: [../../proposal.md](../../proposal.md)
- Design: [../../design.md](../../design.md)
- Tasks: [../../tasks.md](../../tasks.md)
- Spec delta: [../../specs/cli-tool-architecture/spec.md](../../specs/cli-tool-architecture/spec.md)
- Research: [../research/2026-03-02-diagnostics-contract-baseline.md](../research/2026-03-02-diagnostics-contract-baseline.md)
- Design package: [../design/README.md](../design/README.md)

## Реализационные принципы
- Не менять drift/policy semantics, менять только diagnostics contract/presentation layer.
- Поддержать dual output mode: plain-text default + JSON machine-readable.
- Все новые/измененные diagnostics должны быть детерминированы по коду, порядку и summary.

## Suggested Order
1. Phase 01: общий serializer + CLI JSON entrypoints.
2. Phase 02: compatibility/drift alignment + determinism.
3. Phase 03: docs/tests sync + strict validation.

## Definition of Done (Implement)
- Unified diagnostics envelope работает в `validate|diff|gen --check|gen`.
- Документация обновлена и согласована с тестами.
- Все релевантные тесты проходят.
- OpenSpec change остается strict-valid.
