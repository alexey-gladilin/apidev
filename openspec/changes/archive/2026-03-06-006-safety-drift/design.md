## Контекст
Roadmap Horizon 1 фиксирует обязательность закрытия safety/drift gap по удалению stale generated artifacts. Текущий baseline подтверждает отсутствие `REMOVE` в generation plan и фильтрацию drift только по `ADD/UPDATE`.

## Цели / Не-цели
- Цели:
  - определить контракт `REMOVE` для `diff`, `gen --check`, `gen`;
  - сохранить write-boundary policy и детерминизм при операциях удаления;
  - зафиксировать diagnostics и verification matrix для remove/conflict сценариев.
- Не-цели:
  - реализация production-кода в рамках proposal-команды;
  - пересмотр ownership boundary между generated и manual зонами.

## Решения
- `REMOVE` проектируется как first-class change type generation-плана с read-only preview в `diff` и `gen --check`.
- В apply-режиме `apidev gen` удаление допускается только внутри generated root и проходит через safety guard.
- Drift-status/exit semantics сохраняют текущий CLI-контракт, но расширяются на remove-only кейсы.
- Канонический каталог diagnostics фиксируется как `remove-conflict` и `remove-boundary-violation` с обязательной схемой полей `code`, `location`, `detail`.

## Риски / Компромиссы
- Риск: ложные удаления при некорректном определении stale artifact.
  - Митигация: детерминированное построение expected artifact set и strict boundary checks.
- Риск: расхождение diagnostics между сервисным и CLI-слоем.
  - Митигация: фиксированный mapping diagnostic codes и единый regression-набор.

## Предпосылки / зависимости implement-фазы
- CI и локальные проверки опираются на фиксированный machine-readable формат diagnostics (`code`, `location`, `detail`) без неявных преобразований.
- Транзакционный rollback apply находится вне scope данного change-пакета; в ошибочных remove-сценариях применяется safe-fail модель с `drift-status: error` и последующим повторным запуском.

## Linked Artifacts
- Research: [artifacts/research/2026-02-28-safety-drift-remove-baseline.md](./artifacts/research/2026-02-28-safety-drift-remove-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/safety-drift/spec.md](./specs/safety-drift/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды (`/openspec-implement` или `/openspec-implement-single`).
