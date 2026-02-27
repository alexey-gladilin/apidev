# Implementation Handoff

## Preconditions
- Proposal/Design/Plan артефакты утверждены.
- `openspec validate 005-contract-evolution-integration --strict --no-interactive` проходит успешно.

## Recommended Execution Order
1. Реализовать Phase 01: taxonomy + classification mapping.
2. Реализовать Phase 02: optional dbspec adapter + deterministic merge.
3. Реализовать Phase 03: deprecation lifecycle + reporting.
4. Закрыть Verification: unit/contract/integration matrix + docs sync.

## Must-Have Verification
- `uv run pytest tests/unit`
- `uv run pytest tests/contract`
- `uv run pytest tests/integration`
- `openspec validate 005-contract-evolution-integration --strict --no-interactive`

## Delivery Notes
- Сохранять strict separation generated/manual code.
- Не делать `dbspec` обязательной runtime зависимостью.
- Держать default CLI UX backward-compatible; fail-on-breaking режим вводить как явную opt-in/explicit policy.
