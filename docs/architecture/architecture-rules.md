# Architecture Rules And Validation

## Цель

Зафиксировать архитектурные правила APIDev так, чтобы их можно было проверять автоматически и использовать для контроля архитектурных нарушений.

## Источники истины

- Спека: `openspec/changes/add-apidev-cli-tool-architecture/specs/cli-tool-architecture/spec.md`
- Архитектурный baseline: `docs/architecture.md`
- План валидации: `docs/architecture/validation-blueprint.md`

## Каталог правил

| Rule ID | Правило | Автопроверка сейчас | Целевая проверка |
|---|---|---|---|
| AR-001 | `core` не импортирует `application/commands/infrastructure` | Нет | AST import-graph test |
| AR-002 | `application` не импортирует concrete adapters из `infrastructure` | Нет | Forbidden imports test |
| AR-003 | `core` не выполняет direct I/O и format parsing | Частично нарушается | Purity test + refactoring gate |
| AR-004 | `commands` остаются thin adapters | Нет | LOC/complexity + import checks |
| AR-005 | `diff` не пишет файлы, `generate --check` без side-effects | Частично (integration happy-path) | Contract architecture tests |
| AR-006 | Запись только в generated root | Частично (`SafeWriter`) | Negative boundary tests |
| AR-007 | Пути contracts/templates/generated берутся из единого config source | Нет | Consistency checks |

## Карта разрешенных направлений зависимостей

```text
commands -> application -> core
application -> core.ports
infrastructure -> core.ports/core.models
commands -> infrastructure (composition root)

FORBIDDEN:
core -> application/commands/infrastructure
application -> infrastructure (concrete adapter imports)
core -> filesystem I/O and parsing adapters
```

## Нарушения и их классификация

- `Critical`: нарушение направления зависимостей core или write-boundary policy.
- `Major`: импорт concrete infra в application, нарушение deterministic/check contract.
- `Minor`: рост связности в commands, дублирование config path literals.

## Процедура обновления правил

1. Обновить C4-документы (`c4-container.md`, `c4-components.md`) при смене границ.
2. Обновить `docs/architecture.md` при изменении архитектурного обзора.
3. Обновить/добавить тесты в `tests/unit/architecture/*` и `tests/contract/architecture/*`.
4. Синхронизировать изменения с OpenSpec, если меняется нормативное требование.

