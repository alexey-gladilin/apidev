## Контекст
Roadmap (Horizon 1) требует унифицированный diagnostics contract для всех ключевых CLI-режимов. Текущее состояние смешивает разные диагностические модели и не предоставляет паритетный JSON-интерфейс в `diff/gen`.

## Цели / Не-цели
- Цели:
  - задать единый machine-readable envelope и taxonomy diagnostics codes;
  - обеспечить JSON-паритет для `validate`, `diff`, `gen --check`, `gen`;
  - сохранить deterministic semantics и совместимость с существующими policy/drift правилами.
- Не-цели:
  - изменение логики классификации compatibility;
  - изменение write-boundary и release-state lifecycle;
  - изменение бизнес-правил schema/semantic validation.

## Решения
- Ввести единый JSON envelope верхнего уровня для всех команд:
  - `command`, `drift_status`, `summary`, `diagnostics`, `compatibility` (где применимо), `meta`.
- Нормализовать diagnostics item schema:
  - обязательные: `code`, `severity`, `location`, `message`;
  - опциональные стандартизированные: `category`, `detail`, `source`, `rule`, `hint`.
- Ввести namespace-политику кодов:
  - `validation.*`, `compatibility.*`, `generation.*`, `runtime.*`, `config.*`.
- Сохранить plain-text по умолчанию и добавить machine-readable режим как явно поддерживаемый контракт для CI.

## Риски / Компромиссы
- Риск: существующие CI-парсеры завязаны на текущий free-form text output.
  - Митигация: сохранить text output стабильным и продвигать JSON как канонический integration contract.
- Риск: частичная миграция команд приведет к mixed-contract.
  - Митигация: единый общий formatter/serializer слой и cross-command regression tests.
- Риск: чрезмерно широкий schema усложнит поддержку.
  - Митигация: минимальное обязательное ядро + опциональные поля с четкой документацией.

## Linked Artifacts
- Research: [artifacts/research/2026-03-02-diagnostics-contract-baseline.md](./artifacts/research/2026-03-02-diagnostics-contract-baseline.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды.
