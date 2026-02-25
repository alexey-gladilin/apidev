---
name: openspec-single-agent-implementer
description: Implement approved OpenSpec changes in a single-agent mode (no subagents/Task tool) with internal readiness, testing, security, and QA gates. Use proactively in environments that do not support subagents (for example Codex extension).
---

# OpenSpec Single-Agent Implementer

Run the full OpenSpec implementation workflow with one agent only.
Do not call subagents or Task tool in this skill.

## Inputs

- Change ID in `openspec/changes/<change-id>/`
- Approved proposal context (`proposal.md`, `tasks.md`, optional `design.md`, delta specs)
- Project conventions (`AGENTS.md`, `openspec/AGENTS.md`, `README.md`)

## Workflow

### Phase 1: Initialization

1. Validate change:
   - `openspec show <change-id> --json --deltas-only`
   - `openspec validate <change-id> --strict --no-interactive`
2. Load context:
   - `openspec/changes/<change-id>/proposal.md`
   - `openspec/changes/<change-id>/tasks.md`
   - `openspec/changes/<change-id>/design.md` (if present)
   - `openspec/changes/<change-id>/specs/*/spec.md`
3. Pre-flight checks:
   - Coding conventions are documented.
   - Test infrastructure and runnable commands are documented.
4. If pre-flight fails, stop with:

```text
WORKFLOW STOPPED: PRE-FLIGHT FAILED
- Missing: <code conventions | test infrastructure>
- Action Required: Document conventions and configure runnable test infrastructure.
```

5. Run internal spec readiness gate and output one of:
   - `SPEC READY`
   - `SPEC REJECTED`

If `SPEC REJECTED`, stop before coding.

### Phase 2: Mode Selection

- `AUTO` (default): implement by waves.
- `STRICT`: one task at a time, full gate sequence per task.
- `BATCH`: implement all pending tasks first, run gates at the end.

Use `STRICT` for high-risk work (security/auth/data migration/public API compatibility).

### Phase 3: Implementation + Internal Gates

In each task or wave:

1. Implement with RED-GREEN-REFACTOR evidence.
2. Run internal Tester gate:
   - Validate handoff completeness.
   - Run project tests.
   - Challenge missing coverage categories.
   - Output `VERIFIED` or `REJECTION (Tester)`.
3. Run internal Security gate:
   - Validate input handling/auth/secrets/dependencies/trust boundaries.
   - Output `SECURITY VERIFIED` or `REJECTION (Security)`.
4. Run internal QA gate:
   - OpenSpec compliance, architecture integrity, maintainability.
   - Output `APPROVED (QA)` or `REJECTION (QA)`.
5. Update `tasks.md` status only after required gate(s) pass.

Rejection handling:
- Retry with fixes up to 3 attempts per task.
- After 3 failed attempts, mark:
  - `[BLOCKED - NEEDS HUMAN REVIEW]`

### Phase 4: Finalization

1. Run project quality gates:
   - format
   - lint
   - tests
2. Ensure `tasks.md` reflects real status.
3. Output completion summary:

```markdown
## OPENSPEC IMPLEMENTATION COMPLETE: <change-id>
- Mode: <AUTO|STRICT|BATCH>
- Tasks: <completed>/<total>
- Quality Gates: <status>
- Blocked Tasks: <list or "None">
```

## Hard Rules

- Never use Task tool or subagent calls in this skill.
- Never mark a task complete before required verification passes.
- Keep edits scoped to approved proposal/tasks/spec deltas.
