---
name: /dbspec-audit-naming
id: dbspec-audit-naming
category: DBSpec
description: Run deterministic naming consistency audit for DBSpec SSOT and generate structured report artifacts.
---
**Guardrails**
- Use skill `.cursor/skills/dbspec-ops-reporter/SKILL.md`.
- Execute from project root.
- Do not create ad-hoc temporary scripts.
- Emit report in DBSpec Report Contract v1 format.
- Write human-facing Markdown report (`*.md`) fully in Russian.

**Steps**
1. Resolve binary: prefer `dbspec`; fallback to `uv run python -m src`.
2. Ensure `.dbspec/` exists; if missing, run `dbspec init` and stop for user confirmation.
3. Run checks:
   - `dbspec validate --target=ssot`
   - inspect `.dbspec/data/tables.jsonl` and `.dbspec/data/columns.jsonl`.
4. Build findings with codes `DBS-NAM-*`.
5. Deduplicate and group findings by rule/object family.
6. Add prioritized `Топ-5 действий`.
7. Write artifacts:
   - `.dbspec/reports/<timestamp>_naming_consistency.md`
   - `.dbspec/reports/<timestamp>_naming_consistency.json`

**Reference**
- Skill: `.cursor/skills/dbspec-ops-reporter/SKILL.md`
- Report contract: `.cursor/skills/dbspec-ops-reporter/references/report-contract-v1.md`
