# 02. Behavior

## Compatibility Classification
- Любое обнаруженное изменение контрактов нормализуется в change set и классифицируется как:
  - `non-breaking`;
  - `potentially-breaking`;
  - `breaking`.
- Классификация применяется одинаково для сценариев `apidev diff` и `apidev gen --check`.
- CLI вывод должен содержать агрегированную summary по категориям и детализированные diagnostics по операциям/полям.
- Для drift-семантики используются нормализованные статусы `drift|no-drift|error` из `docs/reference/cli-contract.md`.

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

## Release State Contract
- Источник истины release state по умолчанию: `.apidev/release-state.json`.
- Путь может быть переопределён через `.apidev/config.toml` (`evolution.release_state_file`).
- Параметр окна deprecation задаётся в `.apidev/config.toml` как `evolution.grace_period_releases` (default `2`, минимум `1`).
- Формат `.apidev/release-state.json`: JSON-объект с обязательными `release_number` (`int >= 1`) и `baseline_ref` (`git tag` или `git sha`), плюс опциональные `released_at` (`RFC3339 UTC`), `git_commit` (`40-hex`), `tag` (`string`).
- `apidev diff` и `apidev gen --check` работают в read-only режиме и не модифицируют release state storage.

## Baseline Snapshot Contract
- Baseline для compatibility classification резолвится через `baseline_ref` из VCS/CI (team-wide source of truth).
- Локальный `.apidev/releases/<release_number>/api-snapshot.json` допускается как cache, но не является единственным источником истины.
- Snapshot содержит нормализованную API-модель (operations, request/response schemas, errors, deprecation metadata).
- В `diff`/`gen --check` классификация выполняется только через сравнение `current_normalized_model` с baseline snapshot.
- При отсутствии baseline используется явная диагностика `baseline-missing`; при невалидном формате `baseline-invalid`.
- В `strict` policy отсутствие или невалидность baseline приводит к non-zero exit code.

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
