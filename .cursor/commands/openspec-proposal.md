---
name: /openspec-proposal
id: openspec-proposal
category: OpenSpec
description: Create a detailed OpenSpec proposal/design/tasks package with a linked artifact contour under a change-id.
---
<!-- OPENSPEC:START -->
**Guardrails**
- Do not write production code at proposal stage.
- Proposal/Design/Plan must be detailed and verifiable.
- Implement is a separate phase, not part of proposal/design/plan.
- All supporting artifacts must live inside `openspec/changes/<change-id>/artifacts/`.

**Command Goal**
Create an OpenSpec change package where core files and artifacts are linked and consistent:
- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/*/spec.md`
- `artifacts/research/*`
- `artifacts/design/*`
- `artifacts/plan/*`

**Process**
1. Read context:
   - `openspec/project.md`
   - `openspec list`
   - `openspec list --specs`
2. Choose `change-id` and create structure:
   - `openspec/changes/<change-id>/`
   - `openspec/changes/<change-id>/artifacts/research/`
   - `openspec/changes/<change-id>/artifacts/design/`
   - `openspec/changes/<change-id>/artifacts/plan/`
3. Create or collect research in `artifacts/research/`.
4. Create `proposal.md` (Problem, Goals/Non-Goals, Scope, Risks, Rollout).
5. Create `design.md` (As-Is, To-Be, flows, contracts, security, trade-offs).
6. Create `tasks.md` as a phased execution plan (no code implementation).
7. Create spec deltas in `specs/<capability>/spec.md`.
8. Add traceability links between files:
   - `proposal.md` -> link to research
   - `design.md` -> links to research and design artifacts
   - `tasks.md` -> links to plan phase files
   - `artifacts/plan/README.md` -> links to `tasks.md` and `design.md`
9. Run `openspec validate <change-id> --strict --no-interactive`.

**Requirements for tasks.md**
Each task item must include:
- phase and number;
- scope;
- artifact/output file;
- verification (tests/lint/contracts/security);
- Definition of Done.
- At proposal stage, include planning items only (`[ ]`); do not set execution statuses (`[x]`, `[REJECTED]`, `[BLOCKED]`).

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
<!-- OPENSPEC:END -->
