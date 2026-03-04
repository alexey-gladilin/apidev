# Design Package: 012-integration

## Назначение
Пакет фиксирует архитектурные и поведенческие решения для набора интеграционных улучшений `apidev`:
- независимость `scaffold_dir` от `generated_dir`;
- политика записи scaffold через `scaffold_write_policy`;
- runtime OpenAPI adapter для маршрутизации и метаданных;
- short-form синтаксис `errors[].example`;
- integration profiles в `apidev init`;
- переключатель OpenAPI-расширений `openapi.include_extensions`.

## Состав
- [01-architecture.md](./01-architecture.md) - границы системы, контейнеры, компоненты и инварианты.
- [02-behavior.md](./02-behavior.md) - ожидаемое поведение CLI/config/runtime.
- [03-decisions.md](./03-decisions.md) - ключевые решения, альтернативы и компромиссы.
- [04-testing.md](./04-testing.md) - стратегия валидации, регрессии и детерминизма.
- [05-integration-reference.md](./05-integration-reference.md) - референсный код-контракт integration runtime adapter.
- [06-architecture-rule-transition.md](./06-architecture-rule-transition.md) - запись об обновлении boundary-правила AR-006 и ссылок на синхронизированные архитектурные документы.

## Источники
- Baseline research: [../research/2026-03-03-integration-improvements-baseline.md](../research/2026-03-03-integration-improvements-baseline.md)
- Core design summary: [../../design.md](../../design.md)
- Spec delta: [../../specs/cli-tool-architecture/spec.md](../../specs/cli-tool-architecture/spec.md)

## Ограничения пакета
- Документ описывает только проектные решения и rationale.
- Реализация и production-код не входят в scope.
