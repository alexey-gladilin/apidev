# Plan Package: 013-extend-contract

## Цель
Разбить implement-фазу на проверяемые этапы для расширения contract format APIDev поддержкой schema-driven `request` (`path`, `query`, `body`).

## Фазы
- [phase-01.md](./phase-01.md) - контрактная схема, модель и fail-fast валидация request.
- [phase-02.md](./phase-02.md) - проекция request в `operation_map`, transport и OpenAPI.
- [phase-03.md](./phase-03.md) - тесты, документация и финальная readiness-валидация.
- [implementation-handoff.md](./implementation-handoff.md) - handoff для `/openspec-implement`.

## Verification Workflow
- Проверить связность фазового плана: `phase-01.md` -> `phase-03.md`.
- Проверить синхронизацию `plan <-> design <-> spec delta <-> tasks`.
- Учитывать, что plan-артефакты являются planning-stage snapshot: текущий прогресс реализации фиксируется только в `tasks.md` через статусы `[x]/[ ]` под single-writer контролем orchestrator.
- Прогнать strict validation: `openspec validate 013-extend-contract --strict --no-interactive`.

## Связи
- Tasks tracker: [../../tasks.md](../../tasks.md)
- Core design summary: [../../design.md](../../design.md)
- Design package: [../design/README.md](../design/README.md)
- Spec delta: [../../specs/cli-tool-architecture/spec.md](../../specs/cli-tool-architecture/spec.md)
