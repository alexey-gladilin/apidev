# Implementation Handoff: 001-contract-validation

## Phase Dependencies
1. `P1` (schema baseline) must complete before semantic rule expansion in `P2`.
2. `P2` (semantic + codes) must complete before output contract hardening in `P3`.
3. `P3` finalizes CLI contract and integration coverage for Stage A.

## Implementation Sequence
1. Ввести структурированную diagnostics модель в application boundary.
2. Расширить validate pipeline на schema + semantic rule stages.
3. Добавить code-based mapping и deterministic diagnostics ordering.
4. Добавить CLI JSON mode (`--json`) при сохранении default human mode.
5. Зафиксировать unit/contract/integration tests для новых инвариантов.

## Global Quality Gates
- Tests: `pytest`
- Lint: `ruff check src tests`
- Contracts: validate fixtures covering schema + semantic + json paths
- Security: отсутствие небезопасной интерпретации пользовательских полей в рендеринге diagnostics

## Final Definition of Done for Stage A
- Реализованы strict schema checks.
- Реализованы semantic checks с устойчивыми diagnostic codes.
- Реализован `apidev validate --json` с валидным структурированным output.
- Пройдены согласованные quality gates и OpenSpec validation.
