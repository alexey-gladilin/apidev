---
name: /dbspec-report-migrations
id: dbspec-report-migrations
category: DBSpec
description: Build deterministic migration health report from dbspec migrations commands.
---
**Guardrails**
- Use skill `.cursor/skills/dbspec-ops-reporter/SKILL.md`.
- Do not run destructive migration actions (`upgrade`/`downgrade`).
- Do not create ad-hoc temporary scripts.
- Write human-facing Markdown report (`*.md`) fully in Russian.

**Steps**
1. Resolve binary: prefer `dbspec`; fallback to `uv run python -m src`.
2. Collect required command evidence:
   - `dbspec migrations status`
   - `dbspec migrations current`
   - `dbspec migrations pending`
   - `dbspec migrations history`
3. Map domain issues to `DBS-MIG-*` and infra/runtime failures to `DBS-ENV-*`.
4. Apply status rule: if required commands fail, `status` cannot be `ok`.
5. Aggregate findings and add `Топ-5 действий`.
6. Write artifacts:
   - `.dbspec/reports/<timestamp>_migration_health.md`
   - `.dbspec/reports/<timestamp>_migration_health.json`

**Reference**
- Skill: `.cursor/skills/dbspec-ops-reporter/SKILL.md`
- Report contract: `.cursor/skills/dbspec-ops-reporter/references/report-contract-v1.md`
