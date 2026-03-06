---
name: /bugfix-implement
id: bugfix-implement
category: Engineering
description: Запустить multi-agent workflow для исправления бага или точечной правки без OpenSpec change-id.
argument-hint: [issue-description]
---

**Guardrails**
- Используй этот workflow для bugfix/incident/refactor-fix, когда OpenSpec change не нужен.
- Обязательный pipeline: `codebase-researcher -> coder -> tester -> (security при medium/high риске) -> qa`.
- Сабагенты запускаются только через Task tool (или совместимый spawn/wait API).
- Оркестратор не должен переходить в single-agent реализацию.
- Оркестратор не имеет права самостоятельно редактировать implementation-файлы; только state/artifacts + запуск сабагентов.
- Обязательное персистентное состояние: `.cursor/workflows/bugfix/<run-id>/state.json`.
- После любого шага нужно сохранять `next_action` для resume.

**Subagent Capability Gate (обязателен до любых правок)**
1. Проверь доступность запуска сабагентов:
   - Preferred: `Task` tool с ролью сабагента.
   - Fallback: совместимые API `spawn_agent`/`send_input`/`wait`.
2. Выполни обязательный `probe-run`:
   - запусти минимальный сабагент-пробу (`codebase-researcher`) с no-op заданием;
   - дождись результата и зафиксируй техническое evidence (`task id` или `agent/session id`, verdict token, timestamp) в state.
3. До успешного `probe-run` запрещено:
   - анализировать кодовую базу;
   - запускать команды кроме проверки tooling;
   - редактировать любые файлы.
4. Если ни один механизм недоступен ИЛИ probe не дал валидного evidence, останови workflow немедленно:

```
WORKFLOW STOPPED: SUBAGENT TOOLING UNAVAILABLE
- Required: Task tool или совместимый spawn/wait API
- Action Required: Запустить этот workflow в среде с поддержкой сабагентов.
```

5. В этом failure-режиме запрещено продолжать как single-agent.

**Resume Protocol (обязателен на каждом новом запуске)**
- Сначала прочитай `.cursor/workflows/bugfix/<run-id>/state.json`.
- `next_action` — единственный валидный маркер продолжения.
- Восстанавливай прогресс только из `state.json` + `research.md` + evidence сабагентов, не из памяти диалога.
- Если `status=completed` или `status=paused`, не продолжай автоматически.

**Role Violation Guard**
Если оркестратор обнаружил, что собирается сам редактировать implementation-файлы вместо запуска сабагента, останови workflow:

```
WORKFLOW INVALID: ORCHESTRATOR ROLE VIOLATION
- Reason: /bugfix-implement должен оркестрировать через сабагентов, а не выполнять фикс напрямую.
- Action Required: Продолжить с next_action из state и запустить нужного сабагента.
```

**Steps**
1. Сначала загрузи и прими как обязательный протокол `.cursor/agents/bugfix-orchestrator.md`.
2. Возьми описание проблемы из аргумента команды или из последнего сообщения пользователя.
3. Создай `run-id` формата `YYYYMMDD-HHMM-issue-slug`.
4. Подготовь рабочую папку:
   - `.cursor/workflows/bugfix/<run-id>/`
   - `state.json` (из `.cursor/agents/templates/bugfix-workflow-state.template.json`)
5. Выполни `rehydrate`:
   - если `state.json` уже существует, продолжай строго с `next_action`;
   - если `state.json` отсутствует, стартуй с `next_action=run_research`.
6. Оцени риск и зафиксируй его в state:
   - `low`: локальный фикс без чувствительных зон;
   - `medium`: бизнес-логика/контракт;
   - `high`: security/auth/permissions/secrets/public API/data migration.
7. Запусти `codebase-researcher` и сохрани результат в `research.md`.
8. Запусти `coder` на основе issue + research и потребуй HANDOFF.
9. Запусти gates:
   - всегда `tester`;
   - затем `security` только для `medium/high`;
   - затем `qa`.
10. На любом `REJECTION`:
   - увеличь соответствующий счетчик в state;
   - вернись к `coder` с конкретным feedback;
   - если отклонение >3 раз, поставь `status=paused` и останови workflow.
11. На `APPROVED` выполни final quality commands проекта (`format/lint/test`) и заверши:
   - `status=completed`
   - `next_action=none`
   - очисти runtime-артефакты run:
     - удалить `.cursor/workflows/bugfix/<run-id>/state.json`
     - удалить `.cursor/workflows/bugfix/<run-id>/research.md` (если есть)
     - удалить пустую директорию run
12. Если сессия прервалась/контекст сжался:
   - при следующем запуске обязательно продолжай по `state.json`;
   - не восстанавливай ход работ из памяти диалога.

**Subagent Launch Evidence (обязательно)**
- После каждого запуска сабагента сохраняй в state:
  - `agent_identity_map`
  - `last_subagent_evidence` (роль, tool/API, verdict token, timestamp)
- Валидный evidence обязан включать runtime-идентификатор запуска (`task id` или `agent/session id`).
- Если для обязательного шага pipeline нет evidence запуска сабагента, завершай ошибкой:

```
WORKFLOW STOPPED: SUBAGENT EVIDENCE MISSING
```

**Stop Conditions**
- Нет инструмента запуска сабагентов:
  - `WORKFLOW STOPPED: SUBAGENT TOOLING UNAVAILABLE`
- Поврежден state:
  - `WORKFLOW STOPPED: RECOVERY STATE INVALID`
- Нет достаточных evidence для resume:
  - `WORKFLOW STOPPED: RESUME EVIDENCE MISSING`

**References**
- Оркестратор: `.cursor/agents/bugfix-orchestrator.md`
- Research agent: `.cursor/agents/codebase-researcher.md`
- Coder/Review agents: `.cursor/agents/coder.md`, `.cursor/agents/tester.md`, `.cursor/agents/security.md`, `.cursor/agents/qa.md`
