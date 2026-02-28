# Phase 01 - REMOVE Planning Contract

## Цель
Сформировать единый контракт планирования `REMOVE` и синхронизировать read-only drift semantics между `diff` и `gen --check`.

## Шаги
1. Определить expected generated artifact set и алгоритм выделения stale artifacts.
2. Добавить `REMOVE` в generation plan и deterministic ordering.
3. Согласовать общий drift-предикат (`ADD|UPDATE|REMOVE`) для preview/check.

## Выходы
- Обновленная модель generation plan и поведенческий контракт.
- Набор unit тестов на планирование `REMOVE`.
- Синхронизированные требования в CLI contract (черновая версия).

## Риски и rollback
- Риск: неверная идентификация stale files.
- Rollback: feature-branch revert до baseline `ADD/UPDATE` логики при непрохождении тестов.

## Quality Gate
- Unit tests на `DiffService` и deterministic ordering зелёные.
- `diff` и `gen --check` показывают одинаковый drift-status для remove-only кейса.
