# Plan Package: 012-integration

## Цель
Разбить implement-фазу на проверяемые этапы для внедрения интеграционных улучшений `apidev`.

## Фазы
- [phase-01.md](./phase-01.md) - конфиг, scaffold-policy, схема ошибок.
- [phase-02.md](./phase-02.md) - runtime adapter и OpenAPI extensions toggle.
- [phase-03.md](./phase-03.md) - профили и UX `init`.
- [phase-04.md](./phase-04.md) - стабилизация, документация и выпускной gate.
- [implementation-handoff.md](./implementation-handoff.md) - handoff для `/openspec-implement`.

## Verification Workflow
- Проверить связность фазового плана и handoff: `phase-01.md`..`phase-04.md` + `implementation-handoff.md`.
- Проверить cross-link контур `plan <-> design <-> tasks`.
- Проверить implementation-continuation статус и актуальность remaining execution scope в `tasks.md`.
- Прогнать strict validation: `openspec validate 012-integration --strict --no-interactive`.

## Связи
- Tasks tracker: [../../tasks.md](../../tasks.md)
- Core design summary: [../../design.md](../../design.md)
- Design package: [../design/README.md](../design/README.md)
