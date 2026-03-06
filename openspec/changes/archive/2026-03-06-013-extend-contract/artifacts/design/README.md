# Design Package: 013-extend-contract

## Назначение
Пакет фиксирует архитектурные и поведенческие решения для расширения contract format APIDev поддержкой schema-driven `request`:
- `request.path`
- `request.query`
- `request.body`
- проекция request-метаданных в `operation_map`
- генерация OpenAPI `parameters` и `requestBody` из контракта

## Состав
- [01-architecture.md](./01-architecture.md) - системные границы, контейнеры, компоненты и инварианты.
- [02-behavior.md](./02-behavior.md) - нормативное поведение валидации и генерации.
- [03-decisions.md](./03-decisions.md) - ключевые архитектурные решения и компромиссы.
- [04-testing.md](./04-testing.md) - стратегия тестирования, регрессий и детерминизма.

## Источники
- Proposal: [../../proposal.md](../../proposal.md)
- Spec delta: [../../specs/cli-tool-architecture/spec.md](../../specs/cli-tool-architecture/spec.md)

## Ограничения пакета
- Документ описывает только design-level решения и ожидаемое поведение.
- Реализация, рефакторинг и код-детали не входят в scope этого пакета.
