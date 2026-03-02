## Контекст
`release-state` уже участвует в compatibility/deprecation логике (`release_number`, `baseline_ref`), но текущий lifecycle неполный: отсутствует автоматический bootstrap и автоматическое обновление при `gen apply`.

## Цели / Не-цели
- Цели:
  - определить детерминированный lifecycle `release-state` для `apidev gen` (apply);
  - сохранить строгий read-only контракт для `apidev diff` и `apidev gen --check`;
  - зафиксировать behavior для сценариев без git/baseline.
- Не-цели:
  - реализация production-кода в рамках proposal-команды;
  - изменение taxonomy compatibility категорий вне release-state контракта.

## Решения
- `apidev gen` (без `--check`) становится точкой auto-create/sync release-state после успешного apply.
- `release_number` инкрементируется только при реально примененных изменениях (`ADD|UPDATE|REMOVE`).
- `baseline_ref` резолвится по приоритету: `CLI --baseline-ref` -> existing `release-state` -> git fallback.
- `diff` и `gen --check` остаются полностью read-only: любые write side effects запрещены.

## Риски / Компромиссы
- Риск: скрытая мутация release-state при ошибочном apply.
  - Митигация: write-after-success policy и отдельные integration tests на failure-path.
- Риск: неоднозначное поведение при недоступном git.
  - Митигация: явная fallback policy + стабильные diagnostics `baseline-missing|baseline-invalid`.

## Linked Artifacts
- Research: [artifacts/research/2026-03-02-release-state-baseline.md](./artifacts/research/2026-03-02-release-state-baseline.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/contract-evolution-integration/spec.md](./specs/contract-evolution-integration/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды.
