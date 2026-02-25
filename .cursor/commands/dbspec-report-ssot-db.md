---
name: /dbspec-report-ssot-db
id: dbspec-report-ssot-db
category: DBSpec
description: Build deterministic SSOT-vs-DB consistency report using dbspec db validation.
---
**Guardrails**
- Use skill `.cursor/skills/dbspec-ops-reporter/SKILL.md`.
- Requires DB connection configured in `.dbspec/config.toml`.
- Do not create ad-hoc temporary scripts.
- Write human-facing Markdown report (`*.md`) fully in Russian.

**Steps**
1. Resolve binary: prefer `dbspec`; fallback to `uv run python -m src`.
2. Run required checks:
   - `dbspec validate --target=db`
   - `dbspec validate --target=ssot` (baseline)
3. Map diagnostics to finding codes `DBS-CNS-*`.
4. Map runtime/environment failures to `DBS-ENV-*`.
5. Aggregate findings and add prioritized `Топ-5 действий`.
6. Write artifacts:
   - `.dbspec/reports/<timestamp>_ssot_db_consistency.md`
   - `.dbspec/reports/<timestamp>_ssot_db_consistency.json`

**Reference**
- Skill: `.cursor/skills/dbspec-ops-reporter/SKILL.md`
- Report contract: `.cursor/skills/dbspec-ops-reporter/references/report-contract-v1.md`
