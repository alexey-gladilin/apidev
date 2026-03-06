# Research: 006-safety-drift REMOVE baseline (2026-02-28)

## Scope
- `src/apidev/application/services/diff_service.py`
- `src/apidev/application/services/generate_service.py`
- `src/apidev/commands/diff_cmd.py`
- `src/apidev/commands/generate_cmd.py`
- `src/apidev/infrastructure/output/writer.py`
- `tests/integration/test_generate_roundtrip.py`
- `tests/contract/architecture/test_write_boundary_policy.py`
- `tests/unit/test_diff_service_transport_generation.py`
- `docs/reference/cli-contract.md`
- `docs/process/testing-strategy.md`

## Summary
В текущем baseline generation-план оперирует `ADD/UPDATE/SAME` и не формирует `REMOVE`. Drift-детекция в `diff` и `gen --check` учитывает только `ADD/UPDATE`. Write-boundary enforcement для записи внутрь generated root реализован и покрыт тестами.

## Findings (facts only)
1. `GenerationPlan` заполняется через `_planned_change`, который возвращает только `ADD`, `UPDATE`, `SAME`:
   - `src/apidev/application/services/diff_service.py:538`
   - `src/apidev/application/services/diff_service.py:542`
   - `src/apidev/application/services/diff_service.py:544`
2. `apidev diff` вычисляет измененные элементы фильтром `{"ADD", "UPDATE"}` и печатает `drift/no-drift` исходя из этого фильтра:
   - `src/apidev/commands/diff_cmd.py:74`
   - `src/apidev/commands/diff_cmd.py:78`
   - `src/apidev/commands/diff_cmd.py:88`
3. `GenerateService` в `check=True` ставит `drift` только при наличии `ADD/UPDATE`; apply-режим пишет только `ADD/UPDATE`:
   - `src/apidev/application/services/generate_service.py:44`
   - `src/apidev/application/services/generate_service.py:49`
   - `src/apidev/application/services/generate_service.py:55`
4. `apidev gen --check` возвращает exit `1` только когда `drift_status == "drift"`:
   - `src/apidev/commands/generate_cmd.py:86`
   - `src/apidev/commands/generate_cmd.py:88`
5. Документированный CLI-контракт фиксирует drift/exit матрицу для `diff`, `gen --check`, `gen`:
   - `docs/reference/cli-contract.md:66`
   - `docs/reference/cli-contract.md:70`
   - `docs/reference/cli-contract.md:74`
6. `SafeWriter` запрещает запись в root-path и вне generated root:
   - `src/apidev/infrastructure/output/writer.py:15`
   - `src/apidev/infrastructure/output/writer.py:18`
7. Контрактные тесты покрывают allow/reject boundary-поведение writer:
   - `tests/contract/architecture/test_write_boundary_policy.py:13`
   - `tests/contract/architecture/test_write_boundary_policy.py:23`
   - `tests/contract/architecture/test_write_boundary_policy.py:32`
8. Интеграционные drift-тесты покрывают сценарии изменения контракта/описаний, но не содержат remove-case:
   - `tests/integration/test_generate_roundtrip.py:131`
   - `tests/integration/test_generate_roundtrip.py:200`
   - `tests/integration/test_generate_roundtrip.py:269`

## Open Questions
- В текущем scope не найдено кода/теста, где `change_type` принимает `REMOVE`.
- Нужен явный diagnostic code set для remove-конфликтов в CI-friendly формате.

## Fact / Inference
- Fact: в текущей реализации `_planned_change` не генерирует `REMOVE`.
- Fact: drift-фильтрация в `diff`/`gen` основана на `ADD/UPDATE`.
- Fact: write-boundary policy на запись существует и тестируется.
- Inference: для выполнения Horizon 1 необходима явная интеграция `REMOVE` в план, drift-status и apply semantics.
