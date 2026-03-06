## Context

Этап C фокусируется на governance-уровне для операций `diff/generate`: безопасность записи, детерминизм плана генерации, дрейф-контроль и прозрачные условия failure.
Исследовательский baseline показывает, что ключевые механизмы уже есть в коде, но их необходимо оформить как формальный проектный контракт и дополнить недостающими проверками.

## Goals / Non-Goals

- Goals:
  - формализовать архитектурные границы safety-контура для `validate -> diff -> gen`;
  - зафиксировать поведенческие требования drift governance и write safety;
  - определить тестовый и quality gate минимум для implement-фазы.
- Non-Goals:
  - расширение domain/transport фич вне safety-governance периметра;
  - рефакторинг шаблонов генерации как самостоятельная цель;
  - внедрение production-кода в рамках proposal/design workflow.

## Design Summary

- Safety governance рассматривается как сквозной контракт: preflight validation, immutable preview (`diff`/`gen --check`) и controlled apply (`gen`).
- Drift governance задается через deterministic planning + прозрачные сигналы статуса (изменения/отсутствие изменений/ошибки).
- Write boundary фиксируется как жесткий инвариант: запись разрешена только в generated-root с проверяемыми ограничениями.

## Linked Artifacts

- Proposal: [proposal.md](./proposal.md)
- Spec delta: [specs/diff-gen-safety/spec.md](./specs/diff-gen-safety/spec.md)
- Research: [artifacts/research/2026-02-27-diff-gen-safety-baseline.md](./artifacts/research/2026-02-27-diff-gen-safety-baseline.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
