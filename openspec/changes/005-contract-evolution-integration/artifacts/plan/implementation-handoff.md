# Implementation Handoff

## Preconditions
- Proposal/Design/Plan артефакты утверждены.
- `openspec validate 005-contract-evolution-integration --strict --no-interactive` проходит успешно.

## Recommended Execution Order
1. Реализовать Phase 01: taxonomy + classification mapping.
3. Реализовать Phase 03: deprecation lifecycle + release-state contract + reporting.
4. Выполнить Phase 04 blueprint: [phase-04-implementation.md](./phase-04-implementation.md).
5. Закрыть Verification: unit/contract/integration matrix + docs sync.

## Must-Have Verification
- `uv run pytest tests/unit`
- `uv run pytest tests/contract`
- `uv run pytest tests/integration`
- `openspec validate 005-contract-evolution-integration --strict --no-interactive`

## Delivery Notes
- Сохранять strict separation generated/manual code.
- Держать default CLI UX backward-compatible; breaking-aware fail-fast включается через policy `strict` как явную opt-in настройку.
- Использовать `.apidev/config.toml` как canonical config path; не вводить альтернативный `apidev.toml`.
