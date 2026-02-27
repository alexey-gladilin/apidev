# 02. Behavior

## Compatibility Classification
- Любое обнаруженное изменение контрактов нормализуется в change set и классифицируется как:
  - `non-breaking`;
  - `potentially-breaking`;
  - `breaking`.
- Классификация применяется одинаково для сценариев `apidev diff` и `apidev gen --check`.
- CLI вывод должен содержать агрегированную summary по категориям и детализированные diagnostics по операциям/полям.

## Optional DBSpec Integration
- `dbspec` hints используются только как опциональный enrich-layer для type/nullability/reference metadata.
- При отсутствии или недоступности `dbspec` pipeline продолжает работу в baseline-режиме без hard-fail.
- Конфликты между contract data и external hints решаются deterministic policy с приоритетом contract данных.

## Deprecation Lifecycle
- Для эволюционирующих элементов контракта фиксируется lifecycle:
  - `active`;
  - `deprecated`;
  - `removed`.
- Переход `deprecated -> removed` допускается только после объявленного grace периода.
- Удаление элемента без deprecation этапа классифицируется как `breaking`.

## Expected CLI Outcomes
1. `apidev diff`:
- показывает file-level изменения и compatibility summary;
- выделяет deprecation transitions отдельным блоком.

2. `apidev gen --check`:
- сохраняет side-effect-free поведение;
- возвращает non-zero exit code при политике fail-on-breaking и наличии `breaking` changes.

3. `apidev gen`:
- применяет generation plan в текущем safe-write boundary;
- включает deprecation metadata и compatibility traces в generated artifacts там, где это предусмотрено спецификацией.
