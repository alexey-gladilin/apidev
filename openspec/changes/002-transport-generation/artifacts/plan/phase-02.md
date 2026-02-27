# Phase 02 — Template Architecture & Safety

## Цель
Подготовить implement-план эволюции шаблонов и сохранить safety-инварианты генерации.

## Планируемые шаги
1. Декомпозировать изменения template-layer для registry/router/models/errors.
2. Зафиксировать решение по совместимости с текущими generated артефактами.
3. Уточнить acceptance-условия минимально runnable transport layer.
4. Синхронизировать safety policy с write-boundary ограничениями.

## Выходы
- Детализация решений: `artifacts/design/03-decisions.md`
- Поведенческие критерии runnable generation: `artifacts/design/02-behavior.md`
- Фазовый implement-план: `artifacts/plan/phase-02.md`

## Quality Gate
- Зафиксирован deterministic подход к шаблонам.
- Safety policy не допускает перезапись manual-owned файлов.
