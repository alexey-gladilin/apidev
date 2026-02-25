---
name: qa-quality-gate
description: Run a final quality gate for implemented code changes with OpenSpec compliance, architecture integrity, maintainability, and code-quality checks. Use proactively after implementation is complete and before sending the final handoff to the user, especially when source files, tests, or `openspec/changes/*` artifacts were modified.
---

# QA Quality Gate

Perform one final review pass and return a strict PASS/FAIL decision with actionable findings.
Do not rerun implementation in this skill; review what already changed.

## Workflow

1. Run exactly one review pass.
2. Produce one analysis report.
3. Produce one final decision: `APPROVED` or `REJECTION`.

## Preconditions

If a security verification block is required by the current workflow and is missing, stop and return:
`Awaiting Security verification. Cannot review.`

If required test-infrastructure evidence is missing, stop and return:
`Awaiting verified test infrastructure evidence. Cannot review.`

## Project Context Discovery

Read conventions before review:
1. `AGENTS.md` and `openspec/AGENTS.md` if present.
2. Root `README.md`.
3. One primary config file: `Makefile` or `pyproject.toml` or `package.json`.

Do not recursively review all `docs/` unless explicitly requested.

If conventions are absent or ambiguous, reject with:
`Project conventions not documented. Add explicit architecture/layer/dependency rules.`

## Review Checklist

### 1) OpenSpec Compliance
- Confirm all required fields/endpoints/scenarios from relevant spec deltas are implemented.
- Confirm behavior matches requirements, including edge cases.

### 2) Code Quality
- No hardcoded values where configuration is expected.
- No unexplained magic numbers.
- No stubs or placeholder implementations.
- No lingering `TODO` markers in production paths.
- No excessive or obvious comments that merely restate code.
- Comments that remain should capture non-obvious intent, invariants, or critical context.
- Avoid duplicated business logic (DRY by intent, not line count).
- Validate inputs at boundaries.
- Ensure no secrets/tokens are exposed.

### 3) Architecture Integrity
- Respect layer boundaries and dependency direction.
- Detect cross-layer leakage or cyclic dependencies.
- Flag god objects/functions and weak decomposition.

### 4) Maintainability
- Use clear naming and coherent module boundaries.
- Keep file structure aligned with project conventions.
- Keep style consistent with existing codebase.

### 5) Security Gate
- Confirm a security review was completed when required by process.
- Fail review if unresolved CRITICAL or MAJOR security findings remain.

## Output Format

Always output this analysis block first:

```markdown
## QA ANALYSIS REPORT
- Task ID: <task-id or "N/A">
- Reviewer: QA
- Scope Reviewed: <files/modules>
- Project Conventions Source: <paths used>
- Test Infrastructure Evidence: <command/status or "N/A">
- Security Gate Evidence: <status or "N/A">

### OpenSpec Compliance
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Code Quality
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Architecture Integrity
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Maintainability
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Summary
- Critical Issues: <count>
- Major Issues: <count>
- Minor Issues: <count>
- Final Recommendation: APPROVE/REJECT
```

Then output exactly one final decision:

If any checklist item fails:
```markdown
## REJECTION (QA)
- Task ID: <task-id or "N/A">
- Severity: CRITICAL / MAJOR / MINOR
- Issues:
  1. [File:Line] <description>
- Required Action: <specific fix instruction>
```

If all checklist items pass:
```markdown
## APPROVED (QA)
- Task ID: <task-id or "N/A">
- OpenSpec Compliance: ✅
- Code Quality: ✅
- Maintainability: ✅
```

## Tasks.md Integration

If the current workflow tracks progress in `openspec/changes/<change-id>/tasks.md`:
- On approval, mark reviewed item complete (`[x]`).
- On rejection, increment rejection tag (`[REJECTED xN]`).
- If already at `x3`, set `[BLOCKED - NEEDS HUMAN REVIEW]` and stop rejection loop.
