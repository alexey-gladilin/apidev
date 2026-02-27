# Поведение: Diff/Generate Safety & Drift Governance

## 1. Validate-first pipeline (`REQ-1`)

- `apidev diff` и `apidev gen` сначала выполняют preflight validation.
- При ошибке validation pipeline немедленно завершается без построения/применения плана.
- Failure-signal детерминирован и пригоден для CI gate.

## 2. Drift governance режимов (`REQ-2`)

- `apidev diff`: read-only preview, возвращает план и статус без записи файлов.
- `apidev gen --check`: вычисляет drift без записи файлов, используется как enforcement в CI.
- `apidev gen`: apply-режим, применяет только разрешенные операции и сообщает итоговый drift-status.

## 3. Write boundary safety (`REQ-3`)

- Любая попытка записи вне `generated-root` отклоняется как safety error.
- Попытка трактовать `generated-root` как файл отклоняется.
- Manual-owned зона остается неизменной во всех режимах.

## 4. Deterministic drift signal (`REQ-4`)

- При неизменных контрактах diff-план эквивалентен по содержанию и порядку.
- Повторный apply-run после успешного применения не генерирует новых изменений.
- Изменение contract-significant metadata всегда дает предсказуемо обнаруживаемый drift.

## 5. Ожидаемые поведенческие контракты CLI

- `diff`: preview-only, non-mutating, deterministic report.
- `gen --check`: non-mutating drift gate.
- `gen`: controlled mutate only under boundary-policy.
- Для всех режимов статус завершения и человекочитаемый отчет согласованы с drift-результатом.

## Assumptions

- Пользовательский workflow в CI опирается на `diff`/`gen --check` как gate, а не на парсинг побочных логов.
- Формат текстового вывода может эволюционировать, но semantics drift-status остается стабильной.
- Промежуточные временные артефакты не считаются mutation generated artifacts, если не входят в workspace target.

## Unresolved Questions

- Нужно ли зафиксировать machine-readable output (например, JSON) как обязательный интерфейс drift-status.
- Должны ли `diff` и `gen --check` иметь строго одинаковые коды завершения при drift/no-drift.
- Требуется ли отдельный сценарий для частично поврежденного generated-root при apply-режиме.
