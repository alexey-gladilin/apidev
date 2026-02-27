## Context
Этап A из `docs/roadmap.md` требует hardening валидации контрактов: strict schema, semantic checks, diagnostic codes и `--json`.
Текущий baseline подтвержден в исследовании: `validate` использует строковые ошибки и покрывает в основном уникальность `operation_id`.

## Goals / Non-Goals
- Goals:
  - определить целевую архитектуру validation pipeline без реализации кода;
  - зафиксировать контракт структурированной диагностики для human/json режимов;
  - зафиксировать тестовую стратегию и quality gates для implement-фазы.
- Non-Goals:
  - реализация transport generation;
  - изменение `diff/gen`, кроме совместимости с новым diagnostics контрактом;
  - выполнение implementation в рамках текущего change-пакета.

## Design Summary
- Валидация декомпозируется на фазы `schema -> semantic -> diagnostics rendering`.
- Диагностика формализуется как структурированная модель с `code`, `severity`, `message`, `location`, `rule`.
- CLI-рендеринг использует один источник данных diagnostics для text/json консистентности.

## Linked Artifacts
- Research baseline: [artifacts/research/2026-02-27-contract-validation-baseline.md](./artifacts/research/2026-02-27-contract-validation-baseline.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
