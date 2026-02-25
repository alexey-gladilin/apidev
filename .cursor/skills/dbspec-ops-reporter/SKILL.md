---
name: dbspec-ops-reporter
description: Run deterministic dbspec operational audits and produce standardized reports for naming consistency, migration health, SSOT-vs-DB consistency, environment readiness, and delta changes. Use when users ask for dbspec health checks, governance reports, naming analysis, migration status diagnostics, or trend comparison between report runs.
---

# DBSpec Ops Reporter

Run DBSpec checks through fixed commands and generate reproducible reports.
Use this skill to keep output stable across LLM models.

## Preconditions

1. Resolve binary:
   - Prefer `dbspec` from PATH.
   - Fallback: `uv run python -m src`.
2. Run from project root (`cwd`).
3. Ensure `.dbspec/` exists. If missing, run `dbspec init` first.

## Determinism Rules (Mandatory)

1. Never create ad-hoc temporary scripts for analysis/report generation.
2. Never write one-off Python files in project root or temp folders for report logic.
3. Use only deterministic, fixed command sequences from `.cursor/commands/dbspec-*.md`.
4. Keep status/score logic aligned with report contract.
5. If environment prevents command execution, classify as environment readiness issue (not domain issue).

## Report Contract (Mandatory)

Always produce both artifacts:
- Markdown report: `.dbspec/reports/<report-id>.md`
- JSON report: `.dbspec/reports/<report-id>.json`

Always follow `references/report-contract-v1.md` exactly.

## Report Types

- `env_readiness`
  - Validate runtime readiness: binary availability, project layout, DB config reachability, migration command operability.
- `naming_consistency`
  - Analyze table/column naming in SSOT (`.dbspec/data/*.jsonl`).
- `migration_health`
  - Analyze migration state using `dbspec migrations status|history|pending|current`.
- `ssot_db_consistency`
  - Validate SSOT vs DB consistency with `dbspec validate --target=db`.
- `combined_health`
  - Merge findings from all relevant reports.
- `delta_health`
  - Compare latest report with previous same-type report and highlight changes.

## Naming Rules (Default)

1. Table and column names must be `snake_case`.
2. No spaces, hyphens, or camelCase in table/column names.
3. Suffix patterns should be consistent (`_id`, `_rk`, `_dt`, `_flg`, `_nm`, `_cd`, `_ts`, `_qnt`).
4. Avoid ambiguous temporary names (`tmp`, `test`, `new1`) unless explicitly allowlisted.
5. Deduplicate equivalent findings and aggregate by rule/object family.

## Output Discipline

1. Markdown report text must be fully in Russian (except technical literals).
2. Always include: `Что проверялось`, `Критерии проверки`, `Ограничения и контекст выполнения`.
3. Always include a prioritized `Топ-5 действий` block.
4. Keep findings actionable and grouped (avoid long unstructured lists).
5. Use deterministic finding codes: `DBS-ENV-*`, `DBS-NAM-*`, `DBS-MIG-*`, `DBS-CNS-*`, `DBS-DEL-*`.
6. Severity is only `error|warning|info`.
7. Mirror scope/criteria in JSON fields (`what_was_checked`, `criteria_used`, `execution_context`).

## Cursor Commands using this skill

- `.cursor/commands/dbspec-report-env-readiness.md`
- `.cursor/commands/dbspec-audit-naming.md`
- `.cursor/commands/dbspec-report-migrations.md`
- `.cursor/commands/dbspec-report-ssot-db.md`
- `.cursor/commands/dbspec-report-full.md`
- `.cursor/commands/dbspec-report-delta.md`
