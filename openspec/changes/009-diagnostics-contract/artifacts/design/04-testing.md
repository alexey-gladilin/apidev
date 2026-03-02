# Testing Strategy: Diagnostics Contract

## Цели проверки
- доказать единый JSON envelope для `validate|diff|gen --check|gen`;
- доказать детерминированность diagnostics порядка и summary;
- доказать отсутствие регрессий в drift/policy/exit semantics;
- доказать совместимость plain-text UX.

## Unit layer
- serializer/mapper tests для нормализации diagnostics fields;
- tests на namespace-политику кодов;
- tests на deterministic sorting и summary counting.

## Integration layer
- CLI integration tests для каждого режима:
  - success;
  - drift;
  - error;
  - policy-block (`strict`).
- Сравнение JSON payload shape между командами.

## Contract/Architecture layer
- при необходимости: contract test на обязательные envelope поля;
- smoke-coverage, что `diff`/`gen --check` остаются read-only.

## Quality gates
- `uv run pytest tests/unit`
- `uv run pytest tests/integration`
- `uv run pytest tests/contract`
- `make docs-check`
- `openspec validate 009-diagnostics-contract --strict --no-interactive`
