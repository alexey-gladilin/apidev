---
name: /openspec-implement-single
id: openspec-implement-single
category: OpenSpec
description: Implement an approved OpenSpec change in single-agent mode (without subagents/Task tool).
---
<!-- OPENSPEC:START -->
**Guardrails**
- Change must be validated and approved before implementation starts.
- Use this command in environments without subagent support (for example Codex extension).
- Do not call subagents or Task tool in this workflow.
- Keep progress synchronized in `openspec/changes/<change-id>/tasks.md`.
- Run internal gates in order: Spec Readiness -> Tester -> Security -> QA.

**Steps**
1. Validate change:
   - `openspec show <change-id> --json --deltas-only`
   - `openspec validate <change-id> --strict --no-interactive`
2. Load context from:
   - `openspec/changes/<change-id>/proposal.md`
   - `openspec/changes/<change-id>/tasks.md`
   - `openspec/changes/<change-id>/design.md` (if present)
   - `openspec/changes/<change-id>/specs/*/spec.md`
   - `openspec/changes/<change-id>/artifacts/research/*` (if present)
   - `openspec/changes/<change-id>/artifacts/design/*` (if present)
   - `openspec/changes/<change-id>/artifacts/plan/*` (if present)
3. Run pre-flight readiness checks (project conventions + test infrastructure). If missing, stop.
   - Include literal deduplication convention in coding gate: repeated path/config literals, magic strings, and allowed-value sets must be extracted into named constants (module-level or shared by reuse scope).
4. Run internal spec readiness gate and continue only on `SPEC READY`.
5. Select mode:
   - `AUTO` (default, wave-based)
   - `STRICT` (per-task full gates)
   - `BATCH` (all coding first, full gates at the end)
6. Implement tasks according to mode using RED-GREEN-REFACTOR evidence.
7. For each completed unit (task or wave), run internal verification gates in this exact order:
   - Tester gate: execute checks using `.cursor/agents/tester.md` checklist and output `VERIFIED` or `REJECTION`.
   - Security gate: execute checks using `.cursor/agents/security.md` checklist and output `SECURITY VERIFIED` or `REJECTION`.
   - QA gate: execute checks using `.cursor/agents/qa.md` checklist (including duplicated-literal constant extraction check) and output `APPROVED` or `REJECTION`.
   - In single-agent mode, treat these as explicit internal stages with separate evidence blocks; do not skip a stage.
8. Update `tasks.md` only after required gates pass.
9. On repeated rejection:
   - Retry up to 3 times
   - Then mark `[BLOCKED - NEEDS HUMAN REVIEW]`
10. Finalization:
   - Run format/lint/tests from project conventions with concrete commands (no placeholders):
     - if `Makefile` has `format`, `lint`, `test` targets, run `make format`, `make lint`, `make test`
     - otherwise run documented project-native equivalents
   - Ensure `tasks.md` status is accurate
   - Output completion summary with completed and blocked tasks

**Reference**
- Multi-agent workflow command: `.cursor/commands/openspec-implement.md`
- Agent protocols: `.cursor/agents/spec-analyst.md`, `.cursor/agents/coder.md`, `.cursor/agents/tester.md`, `.cursor/agents/security.md`, `.cursor/agents/qa.md`
<!-- OPENSPEC:END -->
