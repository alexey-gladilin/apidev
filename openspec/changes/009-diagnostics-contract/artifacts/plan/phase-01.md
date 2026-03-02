# Phase 01: Unified Diagnostics Model and CLI Surface

## Цель
Сформировать единый diagnostics envelope и включить machine-readable режим во всех целевых CLI командах.

## Scope
- Единый diagnostics serializer/mapper.
- Нормализация обязательных и опциональных полей diagnostics.
- JSON surface для `diff` и `gen` с паритетом к `validate`.

## Deliverables
- Обновленные DTO/diagnostics модели.
- Обновленные `validate_cmd.py`, `diff_cmd.py`, `generate_cmd.py`.
- Unit tests для serializer schema.

## Verification
- `uv run pytest tests/unit -k "diagnostic and json"`
- `uv run pytest tests/unit/test_cli_conventions.py`

## Exit Criteria
- Все целевые команды имеют единый machine-readable envelope.
- Обязательные diagnostics поля стабильны и тестируемы.
