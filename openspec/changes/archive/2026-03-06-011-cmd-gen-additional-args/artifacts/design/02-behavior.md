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
- Pattern policy: case-sensitive glob.
- Matching выполняется по стабильным идентификаторам endpoint-а (`operation_id` и `contract_relpath`) по правилу `OR`.
- Невалидный pattern: пустая строка или malformed glob syntax (включая незакрытый `[` character-class).
- Итоговый порядок endpoint-ов после фильтрации совпадает с canonical ordering pipeline.

## 3. Error-path поведение

- Невалидный pattern возвращает deterministic diagnostics и `drift_status=error`.
- Пустой effective set после фильтрации возвращает deterministic diagnostics и `drift_status=error`.
- Diagnostics codes для filter-failure используют namespace `generation.*`.
- В JSON-режиме ошибки фильтрации входят в unified diagnostics envelope.

## 4. Apply/check semantics

- `gen --check`: фильтрация влияет только на вычисляемый план и drift-status.
- `gen` (apply): фильтрация влияет на apply/remove в рамках вычисленного плана.
- Stale-remove в фильтрованном запуске ограничен artifacts effective endpoint set.
- Artifacts endpoint-ов вне effective endpoint set не удаляются только из-за отсутствия endpoint-а в фильтре.
- Existing release-state flow (`auto-create/sync/bump`) сохраняется и срабатывает в текущем контракте `gen apply`.

## 5. Non-goal behavior

- `apidev diff` не изменяется в этом change.
- Формат YAML-контрактов не изменяется.
