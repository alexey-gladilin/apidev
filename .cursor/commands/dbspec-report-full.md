---
name: /dbspec-report-full
id: dbspec-report-full
category: DBSpec
description: Run full deterministic DBSpec operational audit and generate combined health report.
---
**Guardrails**
- Use skill `.cursor/skills/dbspec-ops-reporter/SKILL.md`.
- Run checks in read-only/audit mode.
- Do not create ad-hoc temporary scripts.
- Write human-facing Markdown report (`*.md`) fully in Russian.

**Steps**
1. Run `/dbspec-report-env-readiness` first.
2. If env readiness has blocking `DBS-ENV-*` errors, mark dependent checks as skipped with explicit reason.
3. Run `/dbspec-audit-naming`.
4. Run `/dbspec-report-migrations`.
5. Run `/dbspec-report-ssot-db`.
6. Merge outputs into `combined_health` with grouped findings and `Топ-5 действий`.
7. Write artifacts:
   - `.dbspec/reports/<timestamp>_combined_health.md`
   - `.dbspec/reports/<timestamp>_combined_health.json`

**Reference**
- Skill: `.cursor/skills/dbspec-ops-reporter/SKILL.md`
- Report contract: `.cursor/skills/dbspec-ops-reporter/references/report-contract-v1.md`
