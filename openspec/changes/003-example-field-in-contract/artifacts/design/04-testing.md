# 04. Testing Strategy

## Unit tests
- `tests/unit/test_validate_service.py`
  - positive: `example` проходит для корректных primitive/object/array/enum;
  - negative: type mismatch, enum mismatch, shape mismatch;
  - negative: root-level `examples` отклоняется как unknown field;
  - diagnostics location/rule/code проверяются явно.
- `tests/unit/test_diff_service_transport_generation.py`
  - проверка fingerprint drift при изменении `example` only;
  - проверка deterministic ordering/serialization.

## Integration tests
- `tests/integration/test_generate_roundtrip.py`
  - roundtrip без diff для неизменного контракта с `example`;
  - diff/update при модификации example.
  - OpenAPI output содержит schema-level `example` в response/error metadata.

## Contract/Architecture tests
- При необходимости добавить архитектурный контракт на сохранение deterministic generated output с `example`.

## Planned verification commands
- `uv run pytest tests/unit/test_validate_service.py`
- `uv run pytest tests/unit/test_diff_service_transport_generation.py`
- `uv run pytest tests/integration/test_generate_roundtrip.py`
- `uv run pytest tests/unit/test_documentation_conventions.py`
