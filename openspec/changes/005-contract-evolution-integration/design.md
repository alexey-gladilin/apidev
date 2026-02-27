## Контекст
Этап D из `docs/roadmap.md` включает три направления: compatibility classification, optional `dbspec` integration и formal deprecation policy.
В текущем baseline эти части либо отсутствуют, либо представлены как заготовки (например, `core/rules/compatibility.py`).

## Цели / Не-цели
- Цели:
  - определить единый compatibility contract для CLI сценариев `diff` и `gen --check`;
  - определить границы и формат optional read-only интеграции с `dbspec`;
  - определить формальную deprecation policy для контрактов и generated artifacts.
- Не-цели:
  - реализация production-кода в рамках proposal-команды;
  - обязательная зависимость от `dbspec` для базового workflow;
  - генерация бизнес-логики или перенос ownership DB-артефактов в APIDev.

## Решения
- Compatibility classification проектируется как отдельный слой правил с прозрачным mapping в CLI diagnostics и exit behavior.
- Интеграция с `dbspec` остается опциональной и read-only: отсутствие `dbspec` не блокирует `validate/diff/gen`.
- Deprecation policy фиксирует lifecycle состояний (active -> deprecated -> removed), минимальные сроки и правила контроля breaking transitions.

## Риски / Компромиссы
- Риск: переусложнение UX при добавлении classification и policy-режимов.
  - Митигация: staged rollout и backward-compatible default behavior.
- Риск: нестабильные результаты при недетерминированной обработке внешних hints.
  - Митигация: canonical normalization и deterministic merge-priority.
- Компромисс: ограничиваем первый этап интеграции `dbspec` только metadata hints без runtime coupling.

## Linked Artifacts
- Research: [artifacts/research/2026-02-27-contract-evolution-integration-baseline.md](./artifacts/research/2026-02-27-contract-evolution-integration-baseline.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/contract-evolution-integration/spec.md](./specs/contract-evolution-integration/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды.
