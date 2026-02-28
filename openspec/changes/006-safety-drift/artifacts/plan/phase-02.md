# Phase 02 - REMOVE Apply Safety

## Цель
Реализовать apply-семантику `REMOVE` в `apidev gen` с сохранением boundary-policy и предсказуемых diagnostics.

## Шаги
1. Расширить apply-контур `GenerateService` на `REMOVE` операции.
2. Гарантировать, что remove path всегда валидируется в рамках generated root.
3. Ввести и зафиксировать diagnostic codes для remove-conflict и boundary-violation.

## Выходы
- Сервисный слой apply для `REMOVE`.
- Contract tests на boundary enforcement для удаления.
- Интеграционные сценарии remove/apply/conflict.

## Риски и rollback
- Риск: удаление несуществующего файла приводит к нестабильному результату.
- Rollback: safe-fail с `error` статусом и откатом частичных изменений в рамках транзакции apply (если поддерживается).

## Quality Gate
- `gen` корректно применяет remove-only и mixed-планы.
- Ошибки удаления классифицируются как `error` с machine-readable diagnostics.
