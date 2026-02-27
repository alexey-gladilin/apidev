## Context

Этап B из `docs/roadmap.md` требует перейти от skeleton-генерации к `Transport Generation MVP+`.
Baseline текущего состояния зафиксирован в исследовании: generation pipeline строит `operation_map.py` и router skeleton-файлы, но не генерирует request/response/error models и не задает runnable handler bridge contract.

## Goals / Non-Goals

- Goals:
  - определить целевую архитектуру transport generation без реализации кода;
  - зафиксировать behavior contract для model generation, operation registry и handler bridge;
  - задать quality gates и тестовый минимум для implement-фазы.
- Non-Goals:
  - внедрение compatibility classification и breaking-aware modes (этап C roadmap);
  - генерация business-логики, SQL и policy-правил;
  - реализация production-кода в рамках текущего proposal workflow.

## Design Summary

- Generation pipeline расширяется до deterministic набора generated transport-артефактов: operation registry, router wiring, request/response/error models.
- Вводится явный bridge-контракт между generated transport-слоем и manual handlers, чтобы сохранить ownership границу generated/manual.
- Контракт operation registry фиксируется как стабильный источник связи `operation_id -> transport metadata` для runtime и тестов.

## Linked Artifacts

- Research: [artifacts/research/2026-02-27-transport-generation-baseline.md](./artifacts/research/2026-02-27-transport-generation-baseline.md)
- External style baseline: [../001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md](../001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)

