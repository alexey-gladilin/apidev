# Архитектура APIDev

Этот раздел является точкой входа в архитектурную документацию проекта и задает роль каждого файла в каталоге `docs/architecture/`.

## Роли документов

| Документ | Роль | Статус |
|---|---|---|
| `architecture-overview.md` | архитектурный baseline текущего состояния | Authoritative |
| `architecture-rules.md` | нормативные архитектурные инварианты | Authoritative |
| `c4-context.md` | системный контекст C4 Level 1 | Reference |
| `c4-container.md` | контейнерная модель C4 Level 2 | Reference |
| `c4-components.md` | компонентная модель C4 Level 3 | Reference |
| `patterns-and-naming.md` | rationale и фактические паттерны | Reference |
| `team-conventions.md` | краткие правила для ежедневной работы | Guide |
| `validation-blueprint.md` | план превращения правил в CI-проверки | Reference |

## Что читать в каком порядке

Для быстрого понимания архитектуры:

1. `architecture-overview.md`
2. `architecture-rules.md`
3. `c4-container.md`
4. `c4-components.md`

Для изменения архитектурных границ:

1. `architecture-overview.md`
2. `architecture-rules.md`
3. `validation-blueprint.md`
4. `docs/process/testing-strategy.md`

Для naming и review:

1. `team-conventions.md`
2. `patterns-and-naming.md`

## Правила поддержки

- Нормативные правила формулируются в `architecture-rules.md`.
- `architecture-overview.md` описывает baseline и не дублирует каталог правил.
- C4-документы раскрывают структуру, но не создают новые нормы.
- `team-conventions.md` остается коротким operational cheat sheet.
- При изменении архитектурных границ синхронно обновляются:
  - `architecture-overview.md`
  - `architecture-rules.md`
  - релевантные C4-документы
  - `validation-blueprint.md`
  - архитектурные тесты

## Связь с OpenSpec и тестами

- Поведенческие требования остаются в OpenSpec.
- Repository-wide архитектурные правила отражаются в `architecture-rules.md`.
- Автоматическая проверяемость правил описывается в `validation-blueprint.md`.
- Архитектурные тесты располагаются в `tests/unit/architecture/*` и `tests/contract/architecture/*`.

## Связанные документы

- `docs/README.md`
- `docs/architecture/architecture-overview.md`
- `docs/architecture/architecture-rules.md`
- `docs/process/testing-strategy.md`
