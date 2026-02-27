---
name: /openspec-proposal
id: openspec-proposal
category: OpenSpec
description: Orchestrate full OpenSpec documentation pipeline (proposal -> research -> design -> plan) under a single change-id.
---
<!-- OPENSPEC:START -->
**Guardrails**
- Do not write production code at proposal stage.
- Proposal/Design/Plan must be detailed and verifiable.
- Implement is a separate phase, not part of proposal/design/plan.
- All supporting artifacts must live inside `openspec/changes/<change-id>/artifacts/`.
- Run this workflow as a gated sequence; stop on blocking failures.
- Keep `tasks.md` in planning state only (`[ ]`) during this command.
- Write all generated change documentation in Russian unless the user explicitly requests another language.
- Keep language consistent across `proposal.md`, `design.md`, `tasks.md`, spec deltas, and all `artifacts/*` files for the same change.

**CRITICAL: Subagent Launch Method**

Use the Task tool to launch subagents. Do not use textual @mentions.

Supported subagents in this pipeline:
- `codebase-researcher` (fact-only research)
- `design-architect` (design artifact package)
- `plan-orchestrator` (phased execution plan + tasks sync)

**Command Goal**
Create a complete OpenSpec documentation package where core files and artifacts are linked and consistent:
- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/*/spec.md`
- `artifacts/research/*`
- `artifacts/design/*`
- `artifacts/plan/*`

**Inputs**
- `change-id` (required)
- feature intent/description (required)
- optional research question override

If `change-id` is missing, ask for it and stop.

**Pipeline**
1. Read context:
   - `openspec/project.md`
   - `openspec list`
   - `openspec list --specs`
2. Ensure structure exists:
   - `openspec/changes/<change-id>/`
   - `openspec/changes/<change-id>/artifacts/research/`
   - `openspec/changes/<change-id>/artifacts/design/`
   - `openspec/changes/<change-id>/artifacts/plan/`
3. Create/update core OpenSpec skeleton:
   - `proposal.md`
   - `design.md`
   - `tasks.md`
   - `specs/<capability>/spec.md` delta(s)
4. Research gate (mandatory):
   - Launch Task tool with `subagent_type: "codebase-researcher"`.
   - Provide: research question, scope boundaries, and target paths.
   - Save output under `artifacts/research/YYYY-MM-DD-topic-name.md`.
   - If research is missing evidence or contains recommendations, reject and retry.
5. Design gate (mandatory):
   - Launch Task tool with `subagent_type: "design-architect"`.
   - Inputs: proposal context + approved research artifact(s) + spec delta intent.
   - Generate/refresh:
     - `artifacts/design/README.md`
     - `artifacts/design/01-architecture.md`
     - `artifacts/design/02-behavior.md`
     - `artifacts/design/03-decisions.md`
     - `artifacts/design/04-testing.md`
   - `artifacts/design/01-architecture.md` must include Mermaid C4 diagrams for:
     - Level 1: System Context
     - Level 2: Container
     - Level 3: Component
   - Use fenced `mermaid` blocks, not ASCII sketches, for required architecture diagrams.
6. Plan gate (mandatory):
   - Launch Task tool with `subagent_type: "plan-orchestrator"`.
   - Inputs: proposal + design artifacts + delta specs.
   - Generate/refresh:
     - `artifacts/plan/README.md`
     - `artifacts/plan/phase-01.md`, `phase-02.md`, ...
     - `artifacts/plan/implementation-handoff.md`
   - Sync `tasks.md` with phased plan links (planning checkboxes only).
7. Add traceability links between files:
   - `proposal.md` -> link to research
   - `design.md` -> links to research and design artifacts
   - `tasks.md` -> links to plan phase files
   - `artifacts/plan/README.md` -> links to `tasks.md` and `design.md`
8. Run `openspec validate <change-id> --strict --no-interactive`.
9. Output completion summary:
   - created/updated files
   - unresolved questions
   - readiness for `/openspec-implement`

**Requirements for tasks.md**
Each task item must include:
- phase and number;
- scope;
- artifact/output file;
- verification (tests/lint/contracts/security);
- Definition of Done.
- At proposal stage, include planning items only (`[ ]`); do not set execution statuses (`[x]`, `[REJECTED]`, `[BLOCKED]`).

**Stop Conditions**
- Missing change context or invalid `change-id`.
- Research gate failed (insufficient evidence or out-of-scope output).
- Design/Plan artifact generation failed to produce required files.
- `openspec validate ... --strict` fails after one repair iteration.

**Definition of Ready**
Change is ready for separate Implement phase when:
1. `openspec validate ... --strict` passes.
2. `proposal.md`, `design.md`, `tasks.md`, and spec deltas are fully populated without placeholders.
3. `Linked Artifacts`/cross-links exist between core files and `artifacts/*`.
4. All artifacts are inside the change folder.
5. It is explicitly stated that Implement runs via a separate command.

**Archiving and Validation**
- With `openspec archive <change-id>`, artifacts move with the change because they are inside `openspec/changes/<change-id>/`.
- `openspec validate` primarily validates OpenSpec core structure, so keep links in core files up to date.

**Reference**
- `openspec show <change-id> --json --deltas-only`
- `openspec show <spec-id> --type spec`
- `rg -n "Requirement:|Scenario:" openspec/specs`
- `.cursor/agents/codebase-researcher.md`
- `.cursor/agents/design-architect.md`
- `.cursor/agents/plan-orchestrator.md`
<!-- OPENSPEC:END -->
