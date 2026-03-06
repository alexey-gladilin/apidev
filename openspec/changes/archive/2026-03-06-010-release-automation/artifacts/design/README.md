# Design Artifacts: 010-release-automation

- [01-architecture.md](./01-architecture.md) - архитектурный контур release automation и C4 (L1/L2/L3).
- [02-behavior.md](./02-behavior.md) - поведенческий контракт release workflow: trigger, stages, fail/skip semantics.
- [03-decisions.md](./03-decisions.md) - ключевые решения, альтернативы, assumptions, risks, open questions.
- [04-testing.md](./04-testing.md) - тестовая стратегия, quality gates и traceability к spec scenarios.

Связанные core-файлы:
- [../../proposal.md](../../proposal.md)
- [../../design.md](../../design.md)
- [../../tasks.md](../../tasks.md)
- [../../specs/release-automation/spec.md](../../specs/release-automation/spec.md)
- [../research/2026-03-02-release-automation-baseline.md](../research/2026-03-02-release-automation-baseline.md)

## Coverage Summary
- Multi-OS pipeline (`macOS|Windows|Linux`) для standalone binary.
- Release trigger contract (`release: published` + `workflow_dispatch`).
- Smoke gate перед публикацией release assets.
- Детерминированный artifact naming/versioning.
- Опциональный Homebrew path как изолированный и secret-gated этап.
