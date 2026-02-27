# 03. Decisions

## D1. Centralized Compatibility Taxonomy
- Решение: ввести единый taxonomy-модуль классификации совместимости и использовать его как source of truth для `diff` и `gen --check`.
- Причина: требуется консистентный результат для governance режимов и CI.
- Альтернатива: раздельная классификация по командам.
- Почему отклонено: риск расхождения semantics и дрейфа поведения между командами.

## D2. Optional Read-only DBSpec Adapter
- Решение: интеграцию с `dbspec` ограничить read-only адаптером с graceful fallback.
- Причина: `docs/product/vision.md` фиксирует optional nature интеграции.
- Альтернатива: сделать `dbspec` обязательной зависимостью для совместимости.
- Почему отклонено: ломает standalone workflow и усложняет onboarding.

## D3. Explicit Deprecation Lifecycle
- Решение: ввести формальный lifecycle (`active`, `deprecated`, `removed`) и минимальный grace window перед удалением.
- Причина: нужен управляемый переход без неожиданного breaking поведения.
- Альтернатива: разрешить immediate remove по факту изменения контракта.
- Почему отклонено: не дает предсказуемой миграции для потребителей API.

## D4. Deterministic Merge and Reporting
- Решение: нормализовать внешние hints и объединять их с контрактом по стабильной policy с приоритетом contract fields.
- Причина: сохранение детерминированности generation/diff output.
- Альтернатива: best-effort merge без явного порядка приоритетов.
- Почему отклонено: может приводить к нестабильному output и ложному drift.
