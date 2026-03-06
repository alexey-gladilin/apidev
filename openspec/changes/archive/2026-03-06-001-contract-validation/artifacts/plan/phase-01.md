# Phase 01 — Strict Schema Baseline

## Scope
- Определить strict schema-инварианты для YAML-контрактов.
- Зафиксировать точку исполнения schema checks в validate pipeline.
- Подготовить негативные fixtures для schema-level нарушений.

## Deliverables
- Формальный список schema rules (required fields, type constraints, shape constraints).
- Трассировка schema rules к diagnostics codes.
- Черновой набор unit/contract тестов на schema invalid cases.

## Verification
- `pytest tests/unit -k validate`
- `ruff check src tests`
- Contract fixture review for malformed input cases

## Definition of Done
- Все schema rules перечислены и не конфликтуют с текущим CLI-контрактом.
- Для каждого schema-rule определен ожидаемый diagnostics outcome.
- Подготовлен список тестов на success/failure сценарии schema-фазы.
