# Phase 01 - Schema Extension and Validation Rules

## Цель

Добавить `example` в контрактный формат и зафиксировать strict validation rules.

## Work packages

1. Обновить `SCHEMA_ALLOWED_FIELDS` и связанный unknown-field behavior.
2. Зафиксировать запрет root-level `examples` как unknown-field regression guard.
3. Добавить validation helper для проверки совместимости `example` с declared schema.
4. Убедиться, что diagnostics остаются стабильными по location/order.

## Deliverables

- `src/apidev/core/rules/contract_schema.py`
- unit tests for positive/negative example cases.

## Exit criteria

- `example` допускается только в разрешенных schema-узлах.
- Root-level `examples` отклоняется как unknown field.
- Некорректный `example` выдает детерминированные schema diagnostics.
