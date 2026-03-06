---
name: /openspec-implement
id: openspec-implement
category: OpenSpec
description: Start TDD implementation of an approved OpenSpec change using specialized agents.
---
<!-- OPENSPEC:START -->
**Guardrails**

- Change must be validated and approved before implementation starts
- Uses adaptive gated workflow with three execution modes:
  - `AUTO` (default): checkpoint-based execution for speed/token efficiency
  - `STRICT`: per-task full pipeline for high-risk changes
  - `BATCH`: implement all pending tasks first, run full gates once at end
- **CRITICAL: Launch subagents using Task tool. DO NOT write @mentions in text - use actual Task tool calls.**
- Tracks progress in tasks.md with automatic status updates
- Only orchestrator updates `tasks.md` statuses; subagents return verdicts/evidence only
- Uses persistent orchestration state at `openspec/changes/<change-id>/artifacts/plan/orchestration-state.json`
- If state file is missing, initialize it from `.cursor/agents/templates/orchestration-state.template.json` before any subagent launch
- After every orchestration stage, persist `next_action`, `updated_at`, subagent evidence, and task/blocker counters to the state file
- On every fresh invocation, including after automatic context summarization, rehydrate strictly from `orchestration-state.json` before deciding what to do next
- Handles rejections (3 rejections → `[BLOCKED - NEEDS HUMAN REVIEW]`)
- Runs quality gates (format/lint/test) at finalization
- **MANDATORY:** If subagent tooling is unavailable, STOP workflow and do not implement manually in this command.
- **MANDATORY:** The orchestrator is never allowed to implement checklist tasks itself; it may only read state, update tracking files, and launch subagents.

**CRITICAL: Subagent Launch Method**

**Use the Task tool to call subagents. DO NOT just write @mentions in text - they won't execute.**

To launch a subagent, you MUST call the Task tool (available in your toolset) with these parameters:

1. `subagent_type`: Set to `"spec-analyst"`, `"coder"`, `"tester"`, `"security"`, or `"qa"`
2. `prompt`: Full task description with all context
3. `description`: Short summary of what the agent will do (3-5 words)

**Example Task tool call structure:**

```
Call Task tool with:
- subagent_type: "coder"
- description: "Implement argparse help coloring"
- prompt: "Implement the following task from OpenSpec change 'add-cli-help-coloring':
  Task: <description>
  Context: <proposal, design, specs>
  Follow RED-GREEN-REFACTOR and output HANDOFF when complete."
```

See `.cursor/agents/openspec-implementer.md` for detailed examples.

**Subagent Capability Gate (run before any implementation work)**

1. Detect whether subagent launch tooling is available in the current environment:
   - Preferred: `Task` tool with `subagent_type`.
   - Compatible fallback: native agent APIs (for example `spawn_agent`/`send_input`/`wait`) with explicit role routing to `.cursor/agents/<role>.md`.
2. If neither mechanism is available, STOP immediately with:

   ```
   WORKFLOW STOPPED: SUBAGENT TOOLING UNAVAILABLE
   - Required: Task tool or compatible spawn/wait agent APIs
   - Action Required: Use /openspec-implement-single OR run in an environment with subagent support.
   ```
3. In this failure mode, it is FORBIDDEN to continue with direct single-agent implementation under `/openspec-implement`.

**Prerequisites Check**

1. Validate change exists and passes strict validation
2. Confirm proposal is approved (ask if unclear)
3. Ensure tasks.md is properly formatted with `[ ]` items
4. Verify project conventions and test infrastructure are documented before coding

**Fresh Invocation Resume Protocol**

On every new invocation of `/openspec-implement`, especially after automatic context summarization:

1. Read `openspec/changes/<change-id>/artifacts/plan/orchestration-state.json` before any planning or task execution.
2. Treat `next_action` as the only valid resume marker.
3. Reconstruct progress from persisted files only (`orchestration-state.json`, `tasks.md`, and subagent evidence), never from conversational memory.
4. If `status=completed` or `status=paused`, do not resume execution automatically.
5. If the state requires a pending gate (`tester`, `security`, `qa`, etc.), resume that gate first and do not launch a fresh `coder`.
6. If the agent finds itself about to edit implementation files directly instead of launching a subagent, STOP and report:

   ```
   WORKFLOW INVALID: ORCHESTRATOR ROLE VIOLATION
   - Reason: /openspec-implement must orchestrate via subagents, not implement tasks directly.
   - Action Required: Resume from orchestration-state.json and launch the required subagent for next_action.
   ```

**Steps**

1. Ask for change ID if not provided in the command
2. Run `openspec validate <change-id> --strict --no-interactive` to ensure change is valid
3. Check if `openspec/changes/<change-id>/proposal.md` exists and is approved
4. Initialize or recover orchestration state immediately (mandatory before any other workflow decision):
   - State path: `openspec/changes/<change-id>/artifacts/plan/orchestration-state.json`
   - Template path: `.cursor/agents/templates/orchestration-state.template.json`
   - This step is mandatory on every fresh invocation, including after automatic context summarization.
   - If state file exists:
     - read it first, before loading proposal/design/tasks in full
     - continue strictly from `next_action`
     - treat it as the source of truth for `mode`, `status`, `completed_tasks`, `blocked_tasks`, `rejection_counts`, `agent_identity_map`, and `last_subagent_evidence`
   - If state file does not exist:
     - create it from `.cursor/agents/templates/orchestration-state.template.json`
     - set `change_id=<change-id>`
     - set `updated_at=<ISO-8601>`
     - keep `next_action=run_spec_readiness_gate` unless a prerequisite failure stops the workflow earlier
   - If state is malformed or conflicts with `tasks.md`, STOP with:

     ```
     WORKFLOW STOPPED: RECOVERY STATE INVALID
     - Action Required: repair orchestration-state.json and tasks.md consistency.
     ```
5. Output the recovered resume marker before doing additional work:

   ```
   Resume State: <status>
   Next Action: <next_action>
   Resumed From: openspec/changes/<change-id>/artifacts/plan/orchestration-state.json
   ```
6. Load only the context required for the recovered `next_action`, then expand to the rest of the change context as needed:
   - Read `openspec/changes/<change-id>/proposal.md` (WHY and WHAT)
   - Read `openspec/changes/<change-id>/design.md` (if exists) (technical decisions)
   - Read `openspec/changes/<change-id>/tasks.md` (implementation checklist)
   - Read linked artifacts (if present):
     - `openspec/changes/<change-id>/artifacts/research/*`
     - `openspec/changes/<change-id>/artifacts/design/*`
     - `openspec/changes/<change-id>/artifacts/plan/*`
   - Read relevant spec deltas: `openspec/changes/<change-id>/specs/*/spec.md`
7. Run pre-flight readiness check:
   - Verify project coding conventions are documented (`AGENTS.md`, `openspec/AGENTS.md`, `README`, `docs`, contribution guides)
   - Verify test infrastructure is configured and runnable (framework + command documented in project config/docs)
   - If missing, STOP with:

     ```
     WORKFLOW STOPPED: PRE-FLIGHT FAILED
     - Missing: <code conventions | test infrastructure>
     - Action Required: Document conventions and configure runnable test infrastructure.
     ```

8. Initialize tracking and output current state:

   ```
   - Artifacts linked: <yes/no>
   - Missing artifact references: <list or none>
   - Orchestration State: openspec/changes/<change-id>/artifacts/plan/orchestration-state.json
   ## OPENSPEC IMPLEMENTATION: <change-id>
   - Proposal: <one line summary>
   - Total Tasks: <count>
   - Pending Tasks: <count of [ ] items>
   - Blocked Tasks: <count of [BLOCKED - NEEDS HUMAN REVIEW] items>
   ```

9. Resolve current-truth sources for readiness consistency check (mandatory):
   - Preferred source: canonical specs under `openspec/specs/*`.
   - Fallback source (when preferred is empty): capability specs from completed changes under `openspec/changes/*/specs/*/spec.md` relevant to the current change dependencies.
   - If `openspec/specs/*` is empty, this MUST be treated as a transitional repository state, not an automatic blocker.
   - Block only when BOTH are missing for relevant capabilities:
     - no canonical `openspec/specs/*`, AND
     - no relevant fallback specs from completed changes.
   - Output evidence before readiness gate:

     ```
     Current Truth Source: <canonical|fallback|mixed>
     Canonical specs found: <count>
     Fallback specs found: <count>
     Relevant capabilities resolved: <list>
     ```

10. Run mandatory spec readiness gate before coding:
   - Call Task tool with:
     - `subagent_type`: `"spec-analyst"`
     - `description`: `"Validate OpenSpec readiness"`
     - `prompt`: include full change context (`proposal.md`, `design.md` if exists, `tasks.md`, delta specs, and resolved current-truth sources from Step 7)
   - Instruct spec-analyst explicitly:
     - use canonical `openspec/specs/*` when available;
     - otherwise use fallback completed-change capability specs for consistency checks;
     - do NOT reject solely because `openspec/specs/*` is empty when fallback evidence exists.
   - Wait for `SPEC READY` or `SPEC REJECTED`
   - If `SPEC REJECTED` → STOP workflow before coding
   - If `SPEC READY` → proceed
   - Log subagent execution evidence in output (agent/tool used + verdict token).
   - Persist to orchestration state:
     - `last_completed_stage=spec_readiness_gate`
     - `next_action=select_execution_mode`
     - append verdict to `last_subagent_evidence`
     - update `agent_identity_map` when runtime agent handle is known

11. Determine execution mode (mandatory):
   - Default mode: `AUTO`
   - Use `STRICT` if any high-risk trigger is present:
     - security/auth/crypto/secrets/permissions changes
     - public API or schema compatibility impact
     - data migration/destructive data operations
     - compliance/safety-critical domain
     - explicit user request for strict per-task gates
   - Print selected mode and reason:

     ```
     Execution Mode: <AUTO|STRICT|BATCH>
     Reason: <risk heuristic or default>
     ```
   - Persist selected mode in orchestration state and set `next_action=execute_tasks`

12. Execute implementation loop based on selected mode:

   **AUTO mode (default, checkpoint-based)**
   - Group pending tasks into logical waves using section/task prefixes from `tasks.md` (for example `1.*`, `2.*`, `3.*`).
   - For each wave:
     - Launch `coder` once for the full wave (do not force one coder run per checkbox item).
     - Record the coder invocation evidence in output (wave IDs + agent/tool handle).
     - Require compact context in coder prompt:
       - current wave task IDs and descriptions
       - changed files and short handoff summary
       - references to proposal/tasks/spec paths (avoid re-pasting full files)
     - Run validation gates by risk:
       - low-risk wave: `tester`
       - medium-risk wave: `tester -> qa`
       - high-risk wave: `tester -> security -> qa`
     - Record gate evidence in output (`VERIFIED` / `SECURITY VERIFIED` / `APPROVED` or `REJECTION`).
     - Mark all wave tasks as `[x]` only after required wave gate(s) return success.
     - After each wave, persist to orchestration state:
       - `completed_tasks`
       - `blocked_tasks`
       - `rejection_counts`
       - `last_completed_stage`
       - `next_action` for the next wave or final gate
       - `last_subagent_evidence`
   - Always run a **final full gate** after last wave:
     - `tester -> security -> qa`

   **STRICT mode (per-task full pipeline)**
   - Process tasks one-by-one exactly as the original strict flow:
     - first `[ ]` task only
     - `coder -> tester -> security -> qa` for that single task
     - update task status and continue

   **BATCH mode (single coding pass, final full gates)**
   - Collect all pending `[ ]` tasks (skip `[BLOCKED - NEEDS HUMAN REVIEW]`, `[x]`).
   - Launch `coder` once with the full pending task set and require:
     - explicit list of completed task IDs
     - RED-GREEN-REFACTOR evidence for each task or coherent cluster
     - consolidated HANDOFF with changed files and tests
   - Do not run intermediate `tester/security/qa` gates while coding is in progress.
   - After coder completes, run full gate sequence once: `tester -> security -> qa`.
   - Update task statuses:
     - If final gate passes, mark completed batch tasks as `[x]`.
     - If final gate fails, mark affected tasks as rejected/blocked per escalation rules and route fixes via `STRICT` mode until resolved.
   - Persist orchestration state after coder handoff and after the final gate.

13. **STRICT single-task execution details (used only in STRICT mode):**

   For each pending task in tasks.md:
   - Find first `[ ]` task (skip `[BLOCKED - NEEDS HUMAN REVIEW]`, `[x]`)
   - **ONLY ONE task at a time** - do not batch or combine tasks
   - **CRITICAL: Launch Coder subagent using Task tool (not @mention in text):**
     - **Call the Task tool** (from your available tools) with these parameters:
       - `subagent_type`: `"coder"`
       - `description`: `"Implement task from OpenSpec change"`
       - `prompt`:

         ```
         Implement the following SINGLE task from OpenSpec change '<change-id>':
         
         Task: <ONLY the current task description from tasks.md - NOT all tasks>
         
         Context:
         - Proposal: openspec/changes/<change-id>/proposal.md
         - Design: openspec/changes/<change-id>/design.md (if exists)
         - Spec Deltas: openspec/changes/<change-id>/specs/
         - Tasks file: openspec/changes/<change-id>/tasks.md
         
         CRITICAL: Follow strict RED-GREEN-REFACTOR methodology:
         1. RED PHASE: Write tests FIRST. Show failing test output before implementation.
         2. GREEN PHASE: Write minimal code to pass tests.
         3. REFACTOR: Improve code while keeping tests passing.
         
         Output HANDOFF block when complete.
         ```
       
       - **⚠️ FORBIDDEN:**
         - Do NOT pass multiple tasks in one prompt
         - Do NOT say "implement all tasks" or "implement tasks.md"
         - Do NOT skip RED PHASE evidence

     - **IMPORTANT:** Wait for Task tool completion.
   - Wait for HANDOFF block from Coder
   - Call Task tool for Tester (`subagent_type: "tester"`) with HANDOFF in prompt
   - Wait for `VERIFIED` or `REJECTION`
   - If `VERIFIED`, call Task tool for Security (`subagent_type: "security"`) with VERIFIED in prompt
   - Wait for `SECURITY VERIFIED` or `REJECTION`
   - If `SECURITY VERIFIED`, call Task tool for QA (`subagent_type: "qa"`) with SECURITY VERIFIED in prompt
   - Monitor the gated pipeline: Coder → Tester → Security → QA
   - Wait for final APPROVED or REJECTION from QA subagent
   - Update task status in tasks.md:
     - If APPROVED → Mark as `[x]`
     - If REJECTED → Increment rejection count
     - If 3 rejections → Mark as `[BLOCKED - NEEDS HUMAN REVIEW]`
   - After each task attempt, persist to orchestration state:
     - `completed_tasks`
     - `blocked_tasks`
     - `rejection_counts`
     - `last_completed_stage`
     - `next_action`
     - `last_subagent_evidence`
   - Continue with next task
14. After all tasks complete or blocked:
   - Detect project quality gates from project docs/config (`AGENTS.md`, `README`, CI workflow, Makefile/package manager/python config`)
   - Resolve concrete commands for execution:
     - if `Makefile` has `format`, `lint`, `test` targets, use `make format`, `make lint`, `make test`
     - otherwise use documented project-native equivalents
   - Run quality gates:

     ```bash
     make format
     make lint
     make test
     ```

   - If any fail → Report issues and mark relevant tasks as `[BLOCKED - NEEDS HUMAN REVIEW]`
   - Persist final gate results to orchestration state with `next_action=generate_completion_summary`
15. Generate completion summary (see format below)

16. Mandatory orchestration audit (before final answer):
   - Confirm at least one invocation for each required stage:
     - readiness: `spec-analyst`
     - implementation: `coder`
     - validation: `tester` (+ `security`/`qa` per selected mode)
   - If any required stage has no subagent invocation evidence, FAIL workflow with:

     ```
     WORKFLOW INVALID: SUBAGENT ORCHESTRATION MISSING
     - Missing stage(s): <list>
     - Action Required: Re-run /openspec-implement with proper subagent execution.
     ```
   - If the audit passes, persist:
     - `status=completed` when no pending/blocking work remains, otherwise `status=active`
     - `last_completed_stage=orchestration_audit`
     - `next_action=none` for completed runs
     - refreshed `updated_at`

**Completion Summary Format**

```
## OPENSPEC IMPLEMENTATION COMPLETE: <change-id>

**Completed:**
- Tasks: X/Y completed
- Quality Gates: [✅/❌] Format, [✅/❌] Lint, [✅/❌] Tests

**Blocked/Pending:**
- [List any blocked or incomplete tasks with reasons]

**Next Steps:**
- [ ] Manual review of blocked items (if any)
- [ ] Commit changes:
  ```bash
  git add openspec/changes/<change-id>/tasks.md <other-files>
  git commit -m "chore: implement <change-id>"
  ```

- [ ] After deployment: Run `openspec archive <change-id> --yes`

```

**Rejection Handling Protocol**

- 1st rejection (from Tester/Security/QA): Call Task tool with `subagent_type="coder"` again, including rejection feedback in prompt
- 2nd rejection: Call Task tool with `subagent_type="coder"` again, including rejection feedback in prompt
- 3rd rejection: Mark task as `[BLOCKED - NEEDS HUMAN REVIEW]` and continue with next task

**Escalation Rules**

- If >30% of tasks blocked → Pause workflow, request human intervention
- If quality gates fail → Report issues, mark relevant tasks as `[BLOCKED - NEEDS HUMAN REVIEW]`
- Continue with remaining tasks even if some are blocked

**Reference**

- Subagent details: `.cursor/agents/openspec-implementer.md`
- Reviewer protocols: `.cursor/agents/tester.md`, `.cursor/agents/security.md`, `.cursor/agents/qa.md`
<!-- OPENSPEC:END -->
