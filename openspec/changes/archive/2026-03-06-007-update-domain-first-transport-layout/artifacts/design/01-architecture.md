# Архитектура: Domain-first Generated Layout

## Контекст
Изменяется только структура generated transport-артефактов и связанные metadata references.
Boundary generated/manual не меняется.

## Изменяемые элементы
- `DiffService`: вычисление target paths и metadata paths.
- Templates (`operation_map`, `router`, `schema`): import/module path под новую структуру.
- Тестовые контракты: обновление expected paths под новый canonical layout.

## Неизменные элементы
- Validate-first pipeline.
- Write-boundary policy.
- Роль `operation_id` как стабильного идентификатора операции.
