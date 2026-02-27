# AI Workflow APIDev

Статус: `Guide`

Этот документ описывает текущий AI workflow в репозитории и должен ссылаться только на реально существующие артефакты и процессы.

## Источники правды

- OpenSpec change-контекст: `openspec/changes/<change-id>/`
- Core-файлы change:
  - `proposal.md`
  - `design.md`
  - `tasks.md`
  - `specs/<capability>/spec.md`
- Артефакты процесса:
  - `artifacts/research/`
  - `artifacts/design/`
  - `artifacts/plan/`
- Правило single writer:
  - только orchestrator обновляет runtime-статусы в `tasks.md`

## Сквозной процесс

1. `Research`
2. `Design`
3. `Plan`
4. `Implement`
5. `Archive`

Рекомендуемый путь:

1. `/openspec-proposal <change-id>`
2. `/openspec-implement <change-id>` или `/openspec-implement-single <change-id>`
3. `/openspec-archive <change-id>` после завершения и деплоя

## Команды и точки входа

### OpenSpec

- `/openspec-proposal` — создает proposal/design/tasks и связанные артефакты исследования
- `/openspec-implement` — основной multi-agent implementation workflow
- `/openspec-implement-single` — single-agent fallback
- `/openspec-archive` — архивирование завершенного change

Legacy/internal helpers:

- `/research-codebase`
- `/design-feature`

### DBSpec

DBSpec operational команды допустимы как отдельный workflow-слой и не меняют основной OpenSpec pipeline.

### Prompt workflow

Для prompt-related сценариев действует отдельный regression reference:

- `docs/process/prompt-improvement-regression-cases.md`

## Роли агентов

### `openspec-implementer`

- координирует pipeline `spec-analyst -> coder -> tester -> security -> qa`
- обновляет runtime-статусы в `tasks.md`
- не делегирует single writer responsibility

### `spec-analyst`

- проверяет готовность spec context к реализации
- не пишет production-код

### `coder`

- реализует назначенный scope
- не обновляет `tasks.md`

### `tester`

- независимо валидирует реализацию тестами
- может добавлять challenge tests, если покрытие явно проседает

### `security`

- выполняет security gate после tester

### `qa`

- выполняет финальный quality/spec/architecture gate

### Research/design/planning helpers

- `codebase-researcher` — fact-only research
- `design-architect` — формирует design artifacts и документирует решения в `design.md` и ADR, если это требуется change-ом
- `plan-orchestrator` — синхронизирует planning artifacts и `tasks.md`

## Gate-модель implement-фазы

Обязательный порядок:

1. Pre-flight
2. Spec readiness
3. Coding
4. Tester gate
5. Security gate
6. QA gate
7. Final quality checks

## Как читать `tasks.md`

Поддерживаемые статусы:

- `[ ]` — pending
- `[x]` — completed
- `[REJECTED xN]` — отклонено N раз
- `[BLOCKED - NEEDS HUMAN REVIEW]` — требуется вмешательство человека

Правило:

- planning-фазы формируют только плановые пункты;
- runtime-статусы выставляет только implement orchestrator.

## Ограничения документа

- Этот guide не подменяет `CONTRIBUTING.md`.
- Этот guide не формулирует новые архитектурные или тестовые нормы.
- Если workflow обещает deliverable, этот deliverable должен реально существовать либо быть описан как artifact class, а не как обязательное имя файла в `docs/`.

## Связанные документы

- `CONTRIBUTING.md`
- `docs/process/testing-strategy.md`
- `docs/process/prompt-improvement-regression-cases.md`
- `openspec/project.md`
