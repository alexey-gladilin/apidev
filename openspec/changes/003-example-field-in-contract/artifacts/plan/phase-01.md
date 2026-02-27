# Phase 01 - Schema Extension and Validation Rules

## Цель

Добавить `example` и endpoint-level `examples` в контрактный формат и зафиксировать strict validation rules.

## Work packages

1. Обновить `SCHEMA_ALLOWED_FIELDS` и связанный unknown-field behavior.
2. Добавить root-level контрактный блок `examples` и его shape validation.
3. Добавить validation helper для проверки совместимости `example` и `examples.*` с declared schema.
4. Убедиться, что diagnostics остаются стабильными по location/order.

## Deliverables

- `src/apidev/core/rules/contract_schema.py`
- unit tests for positive/negative example cases.

## Exit criteria

- `example` допускается только в разрешенных schema-узлах.
- Endpoint-level `examples` принимается в строгом формате и валидируется по связанным schema/error code.
- Некорректный `example` выдает детерминированные schema diagnostics.
