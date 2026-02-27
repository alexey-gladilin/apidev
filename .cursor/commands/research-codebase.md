---
name: /research-codebase
id: research-codebase
category: OpenSpec
description: Legacy helper. Deep fact-only codebase research with artifact storage inside an OpenSpec change.
argument-hint: [change-id] [research-question]
---

# Research Codebase (OpenSpec-bound, Fact-Only)

Status: Legacy helper command. Primary entry point for new flows is `/openspec-proposal`, which runs Research as an internal gate.

Goal: document how the system works today (as-is), without proposing implementation changes.

## Hard Constraints
- Do not propose improvements.
- Do not critique implementation quality.
- Do not design a to-be solution.
- Capture facts only, and clearly label any inference.

## OpenSpec Binding

Research runs in the context of a specific `change-id`.

Store artifacts only here:
- `openspec/changes/<change-id>/artifacts/research/`

If `change-id` is missing or the change does not exist:
- stop and ask to create the change first via `/openspec-proposal`.

## Process

### 1. Intake
Clarify:
- research question;
- boundaries (backend/frontend/infra);
- expected depth level.

### 2. Decomposition
1. Fully read explicitly referenced files.
2. Split work into 2-4 independent tracks.
3. Run parallel tasks through `codebase-researcher` when dependencies allow it.

### 3. Synthesis
1. Merge results.
2. Resolve contradictions.
3. Allow at most one follow-up round.

### 4. Save Artifact
Create file:
`openspec/changes/<change-id>/artifacts/research/YYYY-MM-DD-topic-name.md`

### 5. Sync with OpenSpec Core
Update:
- `openspec/changes/<change-id>/design.md`:
  - add `## Research Inputs` with a link to the new research file.
- `openspec/changes/<change-id>/proposal.md` (if relevant):
  - update context section with research link.

## Research Template

```markdown
---
date: YYYY-MM-DD
researcher: Agent
commit: <short-sha>
branch: <branch>
change_id: <change-id>
research_question: "..."
---

# Research: [Topic]

## Scope
- In scope: ...
- Out of scope: ...
- Assumptions: ...

## Executive Summary
...

## System Map (As-Is)
### [Component]
- Location: `path/to/file:line`
- Responsibility: ...
- Dependencies: ...
- Data Flow: Input -> Processing -> Output

## Critical Execution Paths
1. `file:line` - ...
2. `file:line` - ...

## Contracts and Invariants
...

## Open Questions
...

## Fact / Inference Register
- Fact: ... (Evidence: `file:line`)
- Inference: ... (Based on: `file:line`)
```

## Quality Checklist
1. Key statements are backed by `file:line` evidence.
2. No recommendations or evaluative statements.
3. Explicit Open Questions are present.
4. Research is linked to `change-id` and referenced from OpenSpec core files.
