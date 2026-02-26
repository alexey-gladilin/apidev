---
name: /design-feature
id: design-feature
category: OpenSpec
description: Design feature по фазам Research -> Design -> Plan с прямой привязкой к OpenSpec change-id.
argument-hint: [change-id] [feature-name] [description or ticket link]
---

# Design Feature - Research -> Design -> Plan (OpenSpec-bound, без Implement)

Ты работаешь как архитектор и планировщик. Цель: создать детальный дизайн и фазовый план, строго привязанные к OpenSpec change.

Принцип: сначала факты и архитектурные решения, потом план, только потом отдельная фаза Implement.

## Базовое правило связности с OpenSpec

Все артефакты этой команды хранятся внутри change:
- `openspec/changes/<change-id>/artifacts/research/`
- `openspec/changes/<change-id>/artifacts/design/`
- `openspec/changes/<change-id>/artifacts/plan/`

Ничего не сохраняй в `docs/{feature-name}` для OpenSpec-потока.

## Phase 0. Intake

### 0.1 Аргументы
- `$ARGUMENTS[0]`: `change-id` (обязательный, должен существовать в `openspec/changes/`)
- `$ARGUMENTS[1]`: `feature-name` (slug)
- `$ARGUMENTS[2+]`: описание фичи, тикет, ссылка или полный текст требований

Если `change-id` не передан или change не существует:
1. остановись;
2. попроси сначала запустить `/openspec-proposal`;
3. не генерируй design/plan без change.

### 0.2 Подготовка структуры
Убедись, что существуют папки:
- `openspec/changes/<change-id>/artifacts/research/`
- `openspec/changes/<change-id>/artifacts/design/`
- `openspec/changes/<change-id>/artifacts/plan/`

## Phase 1. Research Gate

1. Используй research из `openspec/changes/<change-id>/artifacts/research/`.
2. Если research нет или он устарел, запусти `/research-codebase` с тем же `change-id`.
3. На вход в дизайн допускай только research с `file:line` ссылками и секцией `Open Questions`.

## Phase 2. Design Artifacts (обязательно)

Сгенерируй в `openspec/changes/<change-id>/artifacts/design/`:
1. `README.md` - контекст, цель, scope, acceptance criteria.
2. `01-architecture.md` - C4 L1/L2/L3, границы слоев, зависимости модулей.
3. `02-behavior.md` - data flow + sequence (happy path + error paths).
4. `03-decisions.md` - ADR-таблица: решение, альтернативы, компромиссы, риски.
5. `04-testing.md` - стратегия тестирования (unit/integration/e2e), тест-кейсы и quality gates.

Условные файлы (если релевантно):
- `05-events.md`
- `06-repo-model.md`
- `07-standards.md`
- `08-api-contract.md`

Документацию пиши на русском языке.

## Phase 3. Human Review Gate (обязательно)

До генерации плана выдай review-пакет:
- что спроектировано;
- ключевые риски;
- открытые вопросы;
- решения, требующие подтверждения.

Если есть критичная неопределенность, остановись и запроси подтверждение.

## Phase 4. Plan (детальный, фазовый, без Implement)

Сгенерируй в `openspec/changes/<change-id>/artifacts/plan/`:
- `README.md`
- `phase-01.md`, `phase-02.md`, ...
- `implementation-handoff.md` (только readiness и порядок, без написания кода)

Каждый `phase-XX.md` должен содержать:
1. Goal
2. Scope (in/out)
3. Files to touch
4. Execution steps (plan-only)
5. Verification
6. Quality gates
7. Risks & rollback
8. Definition of Done

## Phase 5. Sync в OpenSpec core files (обязательно)

Обнови:
1. `openspec/changes/<change-id>/design.md`
   - добавь раздел `## Linked Artifacts`
   - перечисли ссылки на `artifacts/design/*` и ключевой research
2. `openspec/changes/<change-id>/tasks.md`
   - добавь/обнови фазы в виде чекбоксов, согласованных с `artifacts/plan/phase-XX.md`
   - укажи quality gates между фазами
   - явно зафиксируй, что Implement выполняется отдельной командой
   - не проставляй runtime-статусы выполнения (`[x]`, `[REJECTED]`, `[BLOCKED]`) на этапе design/plan

## Ограничения

- Код не писать.
- Реализация только через `/openspec-implement` или `/openspec-implement-single`.

## Критерии готовности

Результат готов, если:
1. Все артефакты лежат внутри `openspec/changes/<change-id>/artifacts/`.
2. `design.md` и `tasks.md` содержат рабочие ссылки на артефакты.
3. План фазовый, проверяемый, с quality gates.
4. Нет рассинхрона между артефактами и OpenSpec core-файлами.
