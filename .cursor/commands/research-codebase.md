---
name: /research-codebase
id: research-codebase
category: OpenSpec
description: Глубокое fact-only исследование кодовой базы с сохранением артефактов в OpenSpec change.
argument-hint: [change-id] [research-question]
---

# Research Codebase (OpenSpec-bound, Fact-Only)

Задача: документировать как система работает сейчас (as-is), без рекомендаций по изменению.

## Жесткие ограничения
- Не предлагай улучшения.
- Не критикуй реализацию.
- Не проектируй to-be.
- Фиксируй только факты и отдельно помеченные выводы.

## Привязка к OpenSpec

Исследование выполняется в контексте конкретного `change-id`.

Артефакты сохраняй только сюда:
- `openspec/changes/<change-id>/artifacts/research/`

Если `change-id` не передан или change не существует:
- остановись и попроси сначала создать change через `/openspec-proposal`.

## Процесс

### 1. Intake
Уточни:
- исследовательский вопрос;
- границы (backend/frontend/infra);
- ожидаемый уровень глубины.

### 2. Декомпозиция
1. Полностью прочитай явно указанные файлы.
2. Разбей задачу на 2-4 независимых направления.
3. Запусти параллельные задачи через `codebase-researcher` там, где нет зависимостей.

### 3. Синтез
1. Объедини результаты.
2. Устрани противоречия.
3. Разрешен максимум 1 follow-up раунд.

### 4. Сохранение
Создай файл:
`openspec/changes/<change-id>/artifacts/research/YYYY-MM-DD-topic-name.md`

### 5. Синхронизация с OpenSpec core
Обнови:
- `openspec/changes/<change-id>/design.md`:
  - добавь `## Research Inputs` с ссылкой на новый research-файл.
- `openspec/changes/<change-id>/proposal.md` (если уместно):
  - обнови раздел контекста ссылкой на research.

## Шаблон исследования

```markdown
---
date: YYYY-MM-DD
researcher: Agent
commit: <short-sha>
branch: <branch>
change_id: <change-id>
research_question: "..."
---

# Research: [Topic]

## Scope
- In scope: ...
- Out of scope: ...
- Assumptions: ...

## Executive Summary
...

## System Map (As-Is)
### [Component]
- Location: `path/to/file:line`
- Responsibility: ...
- Dependencies: ...
- Data Flow: Input -> Processing -> Output

## Critical Execution Paths
1. `file:line` - ...
2. `file:line` - ...

## Contracts and Invariants
...

## Open Questions
...

## Fact / Inference Register
- Fact: ... (Evidence: `file:line`)
- Inference: ... (Based on: `file:line`)
```

## Quality checklist
1. Ключевые тезисы подтверждены `file:line`.
2. Нет советов и оценочных суждений.
3. Есть явные Open Questions.
4. Research привязан к `change-id` и залинкован из OpenSpec core файлов.
