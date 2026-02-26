---
name: /design-feature
id: design-feature
category: OpenSpec
description: Design a feature through Research -> Design -> Plan phases, explicitly bound to an OpenSpec change-id.
argument-hint: [change-id] [feature-name] [description or ticket link]
---

# Design Feature - Research -> Design -> Plan (OpenSpec-bound, no Implement)

You work as an architect and planner. Goal: produce detailed design and phased plan strictly tied to an OpenSpec change.

Principle: facts and architecture decisions first, plan second, implementation in a separate phase.

## Core OpenSpec Binding Rule

All artifacts produced by this command must stay inside the change:
- `openspec/changes/<change-id>/artifacts/research/`
- `openspec/changes/<change-id>/artifacts/design/`
- `openspec/changes/<change-id>/artifacts/plan/`

Do not save OpenSpec workflow artifacts into `docs/{feature-name}`.

## Phase 0. Intake

### 0.1 Arguments
- `$ARGUMENTS[0]`: `change-id` (required, must exist in `openspec/changes/`)
- `$ARGUMENTS[1]`: `feature-name` (slug)
- `$ARGUMENTS[2+]`: feature description, ticket, link, or full requirements text

If `change-id` is missing or does not exist:
1. stop;
2. ask to run `/openspec-proposal` first;
3. do not generate design/plan without a change.

### 0.2 Prepare Structure
Ensure these folders exist:
- `openspec/changes/<change-id>/artifacts/research/`
- `openspec/changes/<change-id>/artifacts/design/`
- `openspec/changes/<change-id>/artifacts/plan/`

## Phase 1. Research Gate

1. Use research from `openspec/changes/<change-id>/artifacts/research/`.
2. If research is missing or outdated, run `/research-codebase` with the same `change-id`.
3. Allow design input only from research that includes `file:line` references and an `Open Questions` section.

## Phase 2. Design Artifacts (Required)

Generate under `openspec/changes/<change-id>/artifacts/design/`:
1. `README.md` - context, goal, scope, acceptance criteria.
2. `01-architecture.md` - C4 L1/L2/L3, layer boundaries, module dependencies.
3. `02-behavior.md` - data flow + sequence (happy path + error paths).
4. `03-decisions.md` - ADR table: decision, alternatives, trade-offs, risks.
5. `04-testing.md` - testing strategy (unit/integration/e2e), test cases, quality gates.

Conditional files (if relevant):
- `05-events.md`
- `06-repo-model.md`
- `07-standards.md`
- `08-api-contract.md`

Write instruction content in English.

## Phase 3. Human Review Gate (Required)

Before generating plan, provide a review package:
- what was designed;
- key risks;
- open questions;
- decisions that require confirmation.

If critical uncertainty remains, stop and request confirmation.

## Phase 4. Plan (Detailed, Phased, no Implement)

Generate under `openspec/changes/<change-id>/artifacts/plan/`:
- `README.md`
- `phase-01.md`, `phase-02.md`, ...
- `implementation-handoff.md` (readiness and sequence only, no code writing)

Each `phase-XX.md` must include:
1. Goal
2. Scope (in/out)
3. Files to touch
4. Execution steps (plan-only)
5. Verification
6. Quality gates
7. Risks & rollback
8. Definition of Done

## Phase 5. Sync to OpenSpec Core Files (Required)

Update:
1. `openspec/changes/<change-id>/design.md`
   - add `## Linked Artifacts`
   - list links to `artifacts/design/*` and key research
2. `openspec/changes/<change-id>/tasks.md`
   - add/update phases as checkboxes aligned with `artifacts/plan/phase-XX.md`
   - include inter-phase quality gates
   - explicitly state that Implement is executed by a separate command
   - do not set runtime execution statuses (`[x]`, `[REJECTED]`, `[BLOCKED]`) during design/plan

## Constraints

- Do not write code.
- Implementation is only through `/openspec-implement` or `/openspec-implement-single`.

## Readiness Criteria

Result is ready when:
1. All artifacts are inside `openspec/changes/<change-id>/artifacts/`.
2. `design.md` and `tasks.md` contain working links to artifacts.
3. Plan is phased, verifiable, and includes quality gates.
4. No drift exists between artifacts and OpenSpec core files.
