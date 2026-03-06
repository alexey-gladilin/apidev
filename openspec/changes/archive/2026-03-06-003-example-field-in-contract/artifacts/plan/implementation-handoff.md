# Implementation Handoff

## Change ID
`003-example-field-in-contract`

## Ready Inputs
- Proposal: [../../proposal.md](../../proposal.md)
- Design: [../../design.md](../../design.md)
- Tasks: [../../tasks.md](../../tasks.md)
- Spec delta: [../../specs/contract-examples/spec.md](../../specs/contract-examples/spec.md)
- Research baseline: [../research/2026-02-27-example-field-baseline.md](../research/2026-02-27-example-field-baseline.md)
- Design package: [../design/README.md](../design/README.md)
- Plan package: [./README.md](./README.md)

## Implement Guidance
- Выполнять задачи строго по фазам из `tasks.md`.
- Сохранять deterministic output policy для generated файлов.
- Не добавлять бизнес-логику в generated слой.
- Проверять validate/diff/gen сценарии в unit + integration тестах.

## Exit from Implement
- Все пункты `tasks.md` закрыты фактами реализации.
- OpenSpec strict validation проходит.
- Change готова к review и последующему архивированию после merge/deploy.
