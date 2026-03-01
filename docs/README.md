# Документация APIDev

Этот раздел задает карту документации APIDev и фиксирует, какой документ является источником истины по каждой теме.

## Как читать документацию

Для нового участника:

1. `README.md` в корне репозитория.
2. `CONTRIBUTING.md`.
3. `docs/product/vision.md`.
4. `docs/architecture/README.md`.
5. `docs/process/testing-strategy.md`.

Для архитектурных изменений:

1. `docs/architecture/README.md`
2. `docs/architecture/architecture-overview.md`
3. `docs/architecture/architecture-rules.md`
4. `docs/architecture/validation-blueprint.md`
5. `openspec/project.md`

Для изменений CLI:

1. `docs/reference/cli-contract.md`
2. `docs/process/testing-strategy.md`
3. `docs/architecture/architecture-overview.md`

Для process- и workflow-изменений:

1. `CONTRIBUTING.md`
2. `docs/process/ai-workflow.md`
3. `docs/process/testing-strategy.md`

## Легенда статусов

- `Authoritative` — нормативный документ, единый источник истины по теме.
- `Reference` — справочный документ, раскрывающий нормы без создания новых норм.
- `Guide` — практическая инструкция или workflow.
- `Draft / Vision` — целевое состояние или гипотеза; не описывает обязательное текущее поведение.
- `Historical` — снимок состояния на дату или архив.

## Карта источников истины

| Тема | Канонический документ | Статус |
|---|---|---|
| Продуктовая рамка и target state | `docs/product/vision.md` | Draft / Vision |
| Архитектурный обзор текущего состояния | `docs/architecture/architecture-overview.md` | Authoritative |
| Архитектурные правила | `docs/architecture/architecture-rules.md` | Authoritative |
| Интеграция generated transport в target app | `docs/architecture/generated-integration.md` | Authoritative |
| Краткие командные соглашения | `docs/architecture/team-conventions.md` | Guide |
| Архитектурные паттерны и нейминг | `docs/architecture/patterns-and-naming.md` | Reference |
| План архитектурной валидации | `docs/architecture/validation-blueprint.md` | Reference |
| Процесс работы с репозиторием | `CONTRIBUTING.md` | Authoritative |
| Тестовая стратегия | `docs/process/testing-strategy.md` | Authoritative |
| AI workflow | `docs/process/ai-workflow.md` | Guide |
| CLI contract | `docs/reference/cli-contract.md` | Authoritative |
| Формат контрактов API | `docs/reference/contract-format.md` | Authoritative |
| Глоссарий | `docs/reference/glossary.md` | Authoritative |
| Дорожная карта | `docs/roadmap.md` | Historical |
| ADR process | `docs/decisions/README.md` | Authoritative |

## Структура разделов

- `docs/product/` — продуктовая рамка и target state.
- `docs/architecture/` — архитектурный baseline, правила и reference-материалы.
- `docs/process/` — процессы разработки, workflow и testing policy.
- `docs/reference/` — точечные контракты и словарь терминов.
- `docs/decisions/` — ADR и принятые архитектурные решения.

## Правила поддержки

- Один нормативный тезис должен быть полностью сформулирован только в одном `Authoritative` документе.
- Остальные документы ссылаются на канонический источник, а не дублируют его.
- Все human-facing документы в `docs/` и `CONTRIBUTING.md` пишутся на русском языке.
- Каноническая команда генерации в документации: `apidev gen`.
- Каждый документ должен явно соответствовать своему статусу: `Authoritative`, `Reference`, `Guide`, `Draft / Vision` или `Historical`.

## Связанные документы

- `CONTRIBUTING.md`
- `docs/product/vision.md`
- `docs/architecture/README.md`
- `docs/process/testing-strategy.md`
- `docs/reference/glossary.md`
