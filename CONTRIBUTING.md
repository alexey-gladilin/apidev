# CONTRIBUTING

Этот документ описывает обязательный процесс работы с репозиторием APIDev и служит единой точкой входа для участников проекта.

## С чего начать

1. Прочитать `AGENTS.md`, если вы работаете через AI-ассистента.
2. Прочитать `docs/README.md`, чтобы понять карту документации.
3. Прочитать `docs/architecture/README.md`, если изменение затрагивает архитектуру.
4. Прочитать `docs/process/testing-strategy.md`, если изменение затрагивает тесты, pipeline или CLI.

## Когда использовать OpenSpec

OpenSpec обязателен, если изменение:

- добавляет новую capability;
- меняет архитектурные границы;
- вводит breaking change;
- меняет нормативные правила проекта;
- требует proposal/design/tasks как traceable-артефакты.

Для таких изменений используйте:

1. `/openspec-proposal <change-id>`
2. `/openspec-implement <change-id>` или `/openspec-implement-single <change-id>`
3. `/openspec-archive <change-id>` после завершения и деплоя

Если изменение ограничивается typo fixes, локальной правкой документации без изменения норм или bug fix без смены intended behavior, proposal обычно не нужен.

## Как вносить изменения в документацию

- Сначала определить канонический документ по теме через `docs/README.md`.
- Новую норму добавлять только в `Authoritative` документ.
- В `Reference` и `Guide` документах давать краткое summary и ссылку на canonical source.
- При изменении архитектурных правил синхронно проверять:
  - `docs/architecture/architecture-overview.md`
  - `docs/architecture/architecture-rules.md`
  - `docs/architecture/team-conventions.md`
  - `docs/architecture/validation-blueprint.md`
- При изменении process-правил синхронно проверять:
  - `CONTRIBUTING.md`
  - `docs/process/ai-workflow.md`
  - `docs/process/testing-strategy.md`

## Где размещать новый документ

- `docs/product/` — продуктовая рамка, vision, non-goals, target state.
- `docs/architecture/` — устройство системы, правила слоев, C4, naming patterns.
- `docs/process/` — workflow, testing policy, operational guidance.
- `docs/reference/` — CLI contracts, glossary, точечные справочники.
- `docs/decisions/` — ADR и закрепленные решения.

Если не удается определить место для документа, сначала обновите `docs/README.md` и только потом добавляйте новый файл.

## Языковая политика

- Документация проекта и process-docs пишутся на русском языке.
- Комментарии, docstrings, identifiers, test names, CLI flags и прочие code artifacts пишутся на английском языке.
- Английские технические термины внутри документа допустимы, но framing и narrative должны быть русскоязычными.

## Как запускать проверки

Минимум перед PR:

1. `uv run pytest`
2. `uv run pytest tests/unit/test_cli_conventions.py` при изменении CLI contract или help/UX
3. `uv run pytest tests/unit/architecture tests/contract/architecture` при изменении архитектурных правил или pipeline
4. `make docs-check` при изменении документации, source-of-truth map или doc paths

Если работаете в OpenSpec change:

1. `openspec validate <change-id> --strict --no-interactive`

## ADR process

Нужно создавать ADR, если изменение:

- меняет информационную архитектуру документации;
- вводит новое постоянное правило проекта;
- фиксирует долгоживущее архитектурное решение;
- отменяет или supersede-ит старое решение.

Правила ADR:

- хранить в `docs/decisions/`;
- использовать формат `ADR-XXXX-<slug>.md`;
- в новых документах ссылаться на superseded ADR, если решение заменено.

## PR checklist

- [ ] Изменение внесено в канонический документ по теме.
- [ ] Дубли и summary-ссылки синхронизированы.
- [ ] Документация на русском, code artifacts на английском.
- [ ] Каноническая команда генерации указана как `apidev gen`.
- [ ] Обновлены связанные process- или architecture-docs, если изменение затрагивает нормы.
- [ ] Обновлены тесты и quality gates, если меняется поведение CLI, pipeline или архитектурных ограничений.
- [ ] Нет ссылок на отсутствующие файлы или несуществующие deliverables.

## Связанные документы

- `docs/README.md`
- `docs/process/testing-strategy.md`
- `docs/process/ai-workflow.md`
- `docs/architecture/README.md`
- `docs/decisions/README.md`
