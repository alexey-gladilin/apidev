# Решения и Trade-offs: Transport Generation MVP+

## Decision 1: Стабилизировать operation registry как первичный runtime контракт
- Контекст: текущее состояние уже генерирует `operation_map.py`, но контракт ограничен `operation_id -> METHOD PATH`.
- Решение: расширить registry contract до структуры, пригодной для transport wiring и тестов, сохранив deterministic ordering.
- Trade-off: рост объема generated metadata компенсируется предсказуемостью drift-проверок.

## Decision 2: Явный bridge между generated transport и manual handlers
- Контекст: roadmap требует стабильный handler bridge contract.
- Решение: фиксировать bridge-подписи в generated artifacts, не перенося в них business logic.
- Trade-off: требуется дисциплина naming/signature policy, но сохраняется безопасная ownership boundary.

## Decision 3: Model generation как часть transport MVP+, а не отдельный plugin-step
- Контекст: request/response/error models перечислены в scope этапа B как базовая цель.
- Решение: включить model generation в основной generation pipeline рядом с routers/registry.
- Trade-off: увеличение ответственности шаблонов, но единая deterministic сборка упрощает CI и onboarding.

## Decision 4: Safety-инварианты write boundary остаются неизменными
- Контекст: действующий SafeWriter и policy generated-root уже покрывают ключевой риск перезаписи manual кода.
- Решение: сохранить текущую boundary policy как обязательный инвариант transport expansion.
- Trade-off: часть интеграционных сценариев требует дополнительного manual wiring, но предотвращается разрушение ручных модулей.
