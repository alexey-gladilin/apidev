---
name: /openspec-proposal
id: openspec-proposal
category: OpenSpec
description: Создать детальный OpenSpec proposal/design/tasks + связанный artifacts-контур в рамках change-id.
---
<!-- OPENSPEC:START -->
**Guardrails**
- Не писать production-код на стадии proposal.
- Proposal/Design/Plan должны быть детальными и проверяемыми.
- Implement - отдельная фаза, не часть proposal/design/plan.
- Все вспомогательные артефакты должны жить внутри `openspec/changes/<change-id>/artifacts/`.

**Цель команды**
Создать OpenSpec change-пакет, где core-файлы и артефакты связаны ссылками и не расходятся:
- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/*/spec.md`
- `artifacts/research/*`
- `artifacts/design/*`
- `artifacts/plan/*`

**Процесс**
1. Прочитать контекст:
   - `openspec/project.md`
   - `openspec list`
   - `openspec list --specs`
2. Выбрать `change-id` и создать структуру:
   - `openspec/changes/<change-id>/`
   - `openspec/changes/<change-id>/artifacts/research/`
   - `openspec/changes/<change-id>/artifacts/design/`
   - `openspec/changes/<change-id>/artifacts/plan/`
3. Сформировать/подтянуть research в `artifacts/research/`.
4. Создать `proposal.md` (Problem, Goals/Non-Goals, Scope, Risks, Rollout).
5. Создать `design.md` (As-Is, To-Be, flows, contracts, security, trade-offs).
6. Создать `tasks.md` как фазовый план (без реализации кода).
7. Создать spec deltas в `specs/<capability>/spec.md`.
8. Добавить трассируемость между файлами:
   - `proposal.md` -> ссылка на research
   - `design.md` -> ссылки на research и design artifacts
   - `tasks.md` -> ссылки на plan phase files
   - `artifacts/plan/README.md` -> ссылки на `tasks.md` и `design.md`
9. Прогнать `openspec validate <change-id> --strict --no-interactive`.

**Требования к tasks.md**
Каждый пункт должен включать:
- фазу и номер;
- scope;
- артефакт/файл результата;
- проверку (tests/lint/contracts/security);
- DoD.
- На стадии proposal фиксируй только плановые пункты (`[ ]`); не проставляй статусы выполнения (`[x]`, `[REJECTED]`, `[BLOCKED]`).

**Definition of Ready**
Change готов к отдельной фазе Implement, если:
1. `openspec validate ... --strict` успешно.
2. `proposal.md`, `design.md`, `tasks.md`, spec deltas заполнены без заглушек.
3. Есть `Linked Artifacts`/ссылки между core-файлами и `artifacts/*`.
4. Все артефакты лежат внутри папки change.
5. Явно зафиксировано: Implement выполняется отдельной командой.

**Архивация и валидация**
- При `openspec archive <change-id>` артефакты переедут вместе с change, т.к. находятся внутри `openspec/changes/<change-id>/`.
- `openspec validate` проверяет прежде всего OpenSpec core-структуру; поэтому следи, чтобы core-файлы содержали актуальные ссылки на артефакты.

**Reference**
- `openspec show <change-id> --json --deltas-only`
- `openspec show <spec-id> --type spec`
- `rg -n "Requirement:|Scenario:" openspec/specs`
<!-- OPENSPEC:END -->
