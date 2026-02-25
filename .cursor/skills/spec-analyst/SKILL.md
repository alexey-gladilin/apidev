---
name: spec-analyst
description: Validate OpenSpec change readiness before implementation by checking completeness, clarity, consistency, and dependency integrity across `proposal.md`, `tasks.md`, and spec deltas. Use proactively before any coding starts for a change and whenever proposal/tasks/spec content is updated.
---

# Spec Analyst

Gate implementation readiness of an OpenSpec change.
Do not implement code in this skill; return `SPEC READY` or `SPEC REJECTED`.

## Inputs

- Change context in `openspec/changes/<change-id>/`
- `openspec/specs/*`
- `openspec/project.md`
- Project conventions from `AGENTS.md`, `openspec/AGENTS.md`, and `README.md`

## Readiness Checks

### 1) Completeness
- Ensure `proposal.md` explains why/what/impact.
- Ensure `tasks.md` contains actionable implementation tasks.
- Ensure spec deltas include requirements with scenarios.

### 2) Clarity
- Ensure requirements are unambiguous and testable.
- Ensure acceptance criteria are explicit.
- Ensure in-scope/out-of-scope boundaries are clear.

### 3) Consistency
- Ensure no contradictions with `openspec/specs/*`.
- Ensure no conflict with `openspec/project.md` conventions.
- Ensure terminology is consistent across proposal/tasks/spec deltas.

### 4) Dependency Integrity
- Ensure tasks have no hidden prerequisites.
- Ensure task ordering is feasible for sequential execution.
- Ensure external assumptions/dependencies are explicitly stated.

## Analysis Report (Mandatory)

```markdown
## SPEC ANALYSIS REPORT
- Change ID: <change-id>
- Reviewer: Spec Analyst
- Scope Reviewed: <proposal/tasks/spec deltas>
- Sources Checked: <openspec/project.md, openspec/specs/*, AGENTS/README>

### Completeness
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Clarity
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Consistency
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Dependency Integrity
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Summary
- Blocking Issues: <count>
- Non-Blocking Issues: <count>
- Final Recommendation: READY/REJECTED
```

## Final Decision

If any blocking issue exists:

```markdown
## SPEC REJECTED
- Change ID: <change-id>
- Blocking Issues:
  1. [File:Line] <issue>
- Required Action:
  1. <specific update to proposal/tasks/spec>
```

Then stop before coding.

If no blocking issues:

```markdown
## SPEC READY
- Change ID: <change-id>
- Readiness: ✅
- Blocking Issues: 0
- Notes: <optional>
```
