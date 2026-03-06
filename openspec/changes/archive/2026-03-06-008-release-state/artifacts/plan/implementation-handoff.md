# Implementation Handoff: 008-release-state

## Ready Inputs
- Proposal: `openspec/changes/008-release-state/proposal.md`
- Design: `openspec/changes/008-release-state/design.md`
- Spec delta: `openspec/changes/008-release-state/specs/contract-evolution-integration/spec.md`
- Plan phases: `artifacts/plan/phase-01.md`, `phase-02.md`, `phase-03.md`

## Implement Priorities
1. Реализовать lifecycle hooks release-state в `gen apply`.
2. Сохранить read-only инварианты `diff` и `gen --check`.
3. Закрыть integration/regression тесты и docs sync.

## Blocking Risks to Watch
- Скрытая запись release-state в read-only режимах.
- Неверный bump `release_number` в no-op run.
- Несогласованность baseline precedence между compare и sync путями.

## Exit Criteria for Implement Phase
- Все задачи в `tasks.md` отмечены как выполненные после фактической реализации.
- Unit/integration tests зелёные.
- Повторный `openspec validate 008-release-state --strict --no-interactive` успешен.
