---
name: /dbspec-report-delta
id: dbspec-report-delta
category: DBSpec
description: Compare latest and previous reports of the same type and produce delta health report with new/fixed/regressed findings.
---
**Guardrails**
- Use skill `.cursor/skills/dbspec-ops-reporter/SKILL.md`.
- Do not create ad-hoc temporary scripts for diff logic.
- Write human-facing Markdown report (`*.md`) fully in Russian.

**Steps**
1. Select report type (`naming_consistency|migration_health|ssot_db_consistency|combined_health`).
2. Locate two latest JSON reports of that type in `.dbspec/reports/`.
3. Compare by finding key: `code + object_ref + rule`.
4. Build delta buckets:
   - `new_issues`
   - `resolved_issues`
   - `regressions`
   - `unchanged_issues`
5. Build report type `delta_health` by contract v1.
6. Write artifacts:
   - `.dbspec/reports/<timestamp>_delta_health.md`
   - `.dbspec/reports/<timestamp>_delta_health.json`

**Reference**
- Skill: `.cursor/skills/dbspec-ops-reporter/SKILL.md`
- Report contract: `.cursor/skills/dbspec-ops-reporter/references/report-contract-v1.md`
