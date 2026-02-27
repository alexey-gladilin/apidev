# Архитектурные Правила APIDev

Статус: `Authoritative`

Этот документ фиксирует архитектурные инварианты APIDev и делит их на обязательные, advisory и будущие кандидаты на автоматизацию.

## Источники истины

- Архитектурный baseline: `docs/architecture/architecture-overview.md`
- План валидации: `docs/architecture/validation-blueprint.md`
- Тестовая стратегия: `docs/process/testing-strategy.md`
- OpenSpec change context, если правило связано с behavior-level изменением

## Обязательные правила

| Rule ID | Правило | Автопроверка сейчас | Статус |
|---|---|---|---|
| AR-001 | `core` не импортирует `application`, `commands`, `infrastructure` | `test_layering_imports.py` | Mandatory / test-backed |
| AR-002 | `application` не импортирует concrete adapters из `infrastructure` | `test_application_no_infra_imports.py` | Mandatory / test-backed |
| AR-003 | `core` не выполняет direct I/O и format parsing | `test_core_purity.py` | Mandatory / test-backed |
| AR-005 | `diff` не пишет файлы, `apidev gen --check` выполняется без side effects | `test_pipeline_contract.py` | Mandatory / test-backed |
| AR-006 | Запись допускается только внутри generated root | `test_write_boundary_policy.py` | Mandatory / test-backed |
| AR-007 | Пути contracts/templates/generated должны идти из единого config source | `test_config_path_single_source.py` | Mandatory / test-backed |
| AR-010 | Документация проекта ведется на русском, code artifacts — на английском | review + doc policy | Mandatory |

## Advisory rules

| Rule ID | Правило | Причина |
|---|---|---|
| AR-004 | `commands` остаются thin adapters | снижение связности и упрощение CLI слоя |
| AR-009 | инварианты модели не должны расползаться из `core` в `application` | удержание domain semantics ближе к модели |

## Future candidate rules

| Rule ID | Кандидат на автоматизацию | Целевая проверка |
|---|---|---|
| AR-008 | boundary parsing не просачивается в `core` как raw format handling | import/pattern checks для YAML/TOML/raw dict parsing |
| AR-004 | thinness `commands` | LOC/complexity guard |
| AR-009 | service bloat vs model invariants | targeted heuristics и review-oriented tests |

## Карта зависимостей

```text
commands -> application -> core
application -> core.ports
infrastructure -> core.ports/core.models
commands -> infrastructure (composition root only)

FORBIDDEN:
core -> application/commands/infrastructure
application -> infrastructure (concrete adapter imports)
core -> filesystem I/O and format parsing
```

## Архитектурные принципы

- APIDev использует selective DDD в `core/*`, а не full-project DDD.
- Boundary parsing и external formats остаются на границе системы.
- `application/*` остается orchestration layer, а не вторым domain layer.
- Generated/manual boundary является обязательной safety policy.
- Документация проекта пишется на русском языке, code artifacts — на английском языке.

## Классификация нарушений

- `Critical` — нарушение направления зависимостей core или write-boundary policy.
- `Major` — concrete infra import в application, нарушение side-effect policy, raw format parsing inside core.
- `Minor` — рост связности в commands, дублирование config literals, локальные нарушения языковой политики.

## Процедура обновления правил

1. Обновить `architecture-overview.md`, если меняется baseline.
2. Обновить этот документ, если меняется нормативное правило.
3. Обновить `validation-blueprint.md`, если меняется автоматизация правила.
4. Обновить архитектурные тесты, если правило должно проверяться автоматически.
5. Проверить согласованность с `docs/process/testing-strategy.md`.
6. Проверить согласованность с `docs/architecture/team-conventions.md`.

## Связанные документы

- `docs/architecture/architecture-overview.md`
- `docs/architecture/validation-blueprint.md`
- `docs/process/testing-strategy.md`
- `docs/reference/glossary.md`
