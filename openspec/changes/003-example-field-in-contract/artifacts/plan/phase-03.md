# Phase 03 - Tests, Docs, and Quality Gate

## Цель

Закрыть change через тесты, документацию и строгую OpenSpec-валидацию.

## Work packages

1. Обновить unit/integration тесты под schema-level и endpoint-level example-сценарии.
2. Обновить `docs/reference/contract-format.md`.
3. Проверить link-traceability между core и artifacts файлами.
4. Выполнить strict validation change-пакета.

## Deliverables

- `tests/unit/test_validate_service.py`
- `tests/unit/test_diff_service_transport_generation.py`
- `tests/integration/test_generate_roundtrip.py`
- `docs/reference/contract-format.md`
- `openspec validate 003-example-field-in-contract --strict --no-interactive`

## Exit criteria

- Все тестовые проверки phase scope проходят.
- Документация консистентна с поведением validate/diff/gen.
- Change готова к отдельному implement этапу.
