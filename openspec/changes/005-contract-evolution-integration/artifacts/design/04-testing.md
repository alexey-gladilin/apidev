# 04. Testing

## Test Matrix
1. Unit tests
- compatibility classifier: positive/negative/edge cases по категориям `non-breaking`/`potentially-breaking`/`breaking`;
- deprecation lifecycle validator: допустимые и запрещенные transitions;
- dbspec adapter normalization/fallback behavior.

2. Contract tests
- подтверждение архитектурных правил (core purity, write boundary, layering) при включении новых extension points;
- проверка side-effect-free инвариантов для `diff` и `gen --check`.

3. Integration tests
- end-to-end сценарии изменения контрактов с compatibility summary;
- сценарии с/без `dbspec` hints при одинаковых контрактах;
- deprecation-to-removal сценарии с ожидаемым classification и CLI exit behavior.

## Quality Gates
- `uv run pytest tests/unit`
- `uv run pytest tests/contract`
- `uv run pytest tests/integration`
- `openspec validate 005-contract-evolution-integration --strict --no-interactive`

## Non-Regression Focus
- deterministic output при одинаковых входах;
- отсутствие side effects у `diff` и `gen --check`;
- backward-compatible default UX при отсутствии fail-on-breaking режима.
