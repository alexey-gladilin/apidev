# Поведение: include/exclude endpoint в `apidev gen`

## 1. Внешнее CLI-поведение

- `apidev gen` принимает повторяемые флаги:
  - `--include-endpoint <pattern>`
  - `--exclude-endpoint <pattern>`
- Если include не задан, candidate set = все endpoint-ы из контрактов.
- Если include задан, candidate set = endpoint-ы, соответствующие include pattern.
- Exclude применяется поверх candidate set и удаляет matching endpoint-ы.

## 2. Precedence и deterministic semantics

- Precedence фиксируется как `include -> exclude`.
- Matching выполняется по стабильным идентификаторам endpoint-а (`operation_id` и `contract_relpath`).
- Итоговый порядок endpoint-ов после фильтрации совпадает с canonical ordering pipeline.

## 3. Error-path поведение

- Невалидный pattern возвращает deterministic diagnostics и `drift_status=error`.
- Пустой effective set после фильтрации возвращает deterministic diagnostics и `drift_status=error`.
- В JSON-режиме ошибки фильтрации входят в unified diagnostics envelope.

## 4. Apply/check semantics

- `gen --check`: фильтрация влияет только на вычисляемый план и drift-status.
- `gen` (apply): фильтрация влияет на apply/remove в рамках вычисленного плана.
- Existing release-state flow (`auto-create/sync/bump`) сохраняется и срабатывает в текущем контракте `gen apply`.

## 5. Non-goal behavior

- `apidev diff` не изменяется в этом change.
- Формат YAML-контрактов не изменяется.

