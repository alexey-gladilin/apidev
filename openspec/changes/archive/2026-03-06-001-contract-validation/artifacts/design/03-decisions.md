# Decisions (Draft ADR)

## D1. Structured diagnostics как boundary contract
- Статус: Proposed
- Решение: заменить строковые ошибки на структурированную модель diagnostics.
- Причина: требуется stable code-based output и `--json` режим.
- Последствия: CLI-представление и тесты переходят на общий diagnostics DTO.

## D2. Two-step validation pipeline
- Статус: Proposed
- Решение: зафиксировать последовательность `schema -> semantic`.
- Причина: прозрачность причин ошибок и масштабируемость rule-набора.
- Последствия: отдельные группы тестов и отдельные rule identifiers.

## D3. Unified diagnostics source for text/json
- Статус: Proposed
- Решение: human и JSON вывод формируются из одной коллекции diagnostics.
- Причина: исключить расхождение между интерактивным и машинным режимами.
- Последствия: добавляется presentation layer в CLI boundary.

## D4. Backward-compatible default UX
- Статус: Proposed
- Решение: human-readable режим остается default без флага.
- Причина: снижение риска регрессий для текущих пользователей.
- Последствия: `--json` становится опциональным расширением, не breaking change.
