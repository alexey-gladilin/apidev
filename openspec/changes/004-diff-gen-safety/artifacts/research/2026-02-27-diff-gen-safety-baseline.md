# Diff/Generate Safety Baseline (2026-02-27)

## Research Scope

- Команды CLI: `diff`, `gen`, `gen --check`
- Application services: `DiffService`, `GenerateService`
- Safety boundary: `SafeWriter`
- Regression coverage: unit/integration tests для drift и идемпотентности
- Документация контракта CLI и testing strategy

## Summary

В текущем состоянии реализованы базовые safety-механизмы для `validate -> diff -> gen`: preflight validation, check-mode drift detection без записи, write-boundary для generated-root и deterministic ordering в diff-плане.

## Findings (Facts Only)

1. `diff` и `gen` выполняют validation до основной логики; при ошибке validation команда завершается `SystemExit(1)`.
2. `GenerateService` использует `DiffService` как источник плана изменений.
3. В `check=True` режим `GenerateService` возвращает drift-результат без записи файлов.
4. В apply-режиме запись выполняется только для `ADD`/`UPDATE` изменений.
5. `SafeWriter` блокирует запись вне generated-root и блокирует запись в generated-root как файл.
6. `DiffService` применяет `ensure_unique_operation_ids` и сортирует операции по `operation_id`.
7. Diff-классификация изменений работает по содержимому: `ADD`/`UPDATE`/`SAME`.
8. Генерируемые metadata включают `contract_fingerprint` на основе канонизированного представления части контракта.
9. Тесты подтверждают deterministic replay и drift detection при изменениях контрактной metadata.
10. Документация фиксирует режимы drift governance и требования write safety как testing policy.

## Code References

- `src/apidev/commands/diff_cmd.py:21`
- `src/apidev/commands/diff_cmd.py:25`
- `src/apidev/commands/generate_cmd.py:22`
- `src/apidev/commands/generate_cmd.py:39`
- `src/apidev/application/services/generate_service.py:30`
- `src/apidev/application/services/generate_service.py:33`
- `src/apidev/application/services/generate_service.py:36`
- `src/apidev/application/services/diff_service.py:35`
- `src/apidev/application/services/diff_service.py:38`
- `src/apidev/application/services/diff_service.py:94`
- `src/apidev/application/services/diff_service.py:173`
- `src/apidev/application/services/diff_service.py:207`
- `src/apidev/infrastructure/output/writer.py:15`
- `src/apidev/infrastructure/output/writer.py:18`
- `tests/unit/test_diff_service_transport_generation.py:152`
- `tests/unit/test_diff_service_transport_generation.py:180`
- `tests/integration/test_generate_roundtrip.py:11`
- `tests/integration/test_generate_roundtrip.py:126`
- `tests/integration/test_generate_roundtrip.py:192`
- `tests/integration/test_generate_roundtrip.py:258`
- `docs/reference/cli-contract.md:49`
- `docs/process/testing-strategy.md:50`

## Open Questions

1. В текущем scope не обнаружен отдельный тест, явно доказывающий отсутствие файловой записи у `apidev diff` через filesystem-spy/snapshot.
2. В текущем scope не обнаружен отдельный тест, явно доказывающий отсутствие файловой записи у `apidev gen --check` через filesystem-spy/snapshot.
3. Формальный spec-контракт порядка `validate -> diff -> gen` отсутствует как отдельная capability-спецификация.

## Fact / Inference

- Fact: раздел Findings и ссылки в Code References основаны на прямом чтении файлов.
- Inference: pipeline-правило `validate -> diff -> gen` выведено из реализации команд и сервисов, а не из отдельного существующего spec-файла.
