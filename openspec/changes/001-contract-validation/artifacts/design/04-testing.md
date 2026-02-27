# Стратегия Тестирования Stage A

## Test Layers
1. Unit (core/application): schema checks, semantic checks, diagnostics mapping.
2. Unit (CLI): human output path, JSON output path, exit code mapping.
3. Contract/Integration: стабильность JSON-структуры и deterministic порядок diagnostics.

## Проверяемые критерии
1. Duplicate `operation_id` возвращает детерминированный `code` и `location`.
2. Schema и semantic нарушения различимы по `rule`/`code`.
3. `apidev validate --json` всегда выдает parseable JSON (success/failure).
4. Human mode не печатает JSON payload.
5. `exit code 1` при наличии `severity=error`, иначе `exit code 0`.
6. Порядок diagnostics стабилен для одинакового набора контрактов.

## Regression Guardrails
- Позитивный сценарий валидного минимального контракта остается зеленым.
- Validate не выполняет запись в generated-зону.
- CLI help/exit behavior не нарушается.
