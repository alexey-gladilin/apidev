---
name: /dbspec-report-env-readiness
id: dbspec-report-env-readiness
category: DBSpec
description: Build environment readiness report for dbspec operations (binary, project, db config, command operability).
---
**Guardrails**
- Use skill `.cursor/skills/dbspec-ops-reporter/SKILL.md`.
- Do not create ad-hoc temporary scripts for checks.
- Write human-facing Markdown report (`*.md`) fully in Russian.

**Steps**
1. Resolve binary (`dbspec` or fallback `uv run python -m src`).
2. Check project readiness:
   - presence of `.dbspec/`
   - readability of `.dbspec/config.toml`
   - presence of data files under `.dbspec/data/`
3. Run operability probes:
   - `dbspec --help`
   - `dbspec validate --target=ssot`
   - `dbspec migrations status`
4. Classify infra/runtime failures as `DBS-ENV-*`.
5. Build report type `env_readiness` by contract v1.
6. Write artifacts:
   - `.dbspec/reports/<timestamp>_env_readiness.md`
   - `.dbspec/reports/<timestamp>_env_readiness.json`

**Reference**
- Skill: `.cursor/skills/dbspec-ops-reporter/SKILL.md`
- Report contract: `.cursor/skills/dbspec-ops-reporter/references/report-contract-v1.md`
