<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## Workflow Index

- Entry points:
  - `/openspec-proposal` as the documentation orchestrator (`proposal -> research -> design -> plan`, plus spec deltas and artifact sync).
  - `/openspec-implement` (multi-agent) or `/openspec-implement-single` (single-agent) for implementation.
  - `/bugfix-implement` as bugfix/refactor-fix multi-agent orchestrator (without OpenSpec change-id).
- Source of truth:
  - Core change files under `openspec/changes/<change-id>/`.
  - Artifact folders under `openspec/changes/<change-id>/artifacts/{research,design,plan}`.
  - `tasks.md` is the execution tracker; only orchestrator updates task statuses (single writer rule).

## Bugfix Workflow (Multi-Agent Only)

- Command: `/bugfix-implement [issue-description]`
- Scope: bugfix/incident/refactor-fix work that does not require an OpenSpec change-id.
- Required pipeline: `codebase-researcher -> coder -> tester -> (security for medium/high risk) -> qa`.
- Orchestrator-only rule: the command acts as coordinator and must not implement fixes directly.
- Mandatory capability gate before any codebase analysis or edits:
  - Preferred tooling: Task tool with subagent routing.
  - Compatible fallback: `spawn_agent`/`send_input`/`wait`.
- Mandatory probe run:
  - launch a minimal `codebase-researcher` subagent task;
  - persist runtime evidence (`task id` or `agent/session id`, verdict token, timestamp).
- If subagent tooling is unavailable or probe evidence is missing, stop immediately:
  - `WORKFLOW STOPPED: SUBAGENT TOOLING UNAVAILABLE`
- If the orchestrator is about to perform direct implementation edits, stop immediately:
  - `WORKFLOW INVALID: ORCHESTRATOR ROLE VIOLATION`
- Persistent resume state is required:
  - `.cursor/workflows/bugfix/<run-id>/state.json`
  - resume strictly from `next_action` and persisted evidence only.

## Repository Conventions

- Project documentation must be written in Russian.
- Code comments, docstrings, identifiers, test names, CLI flags, and other code artifacts must be written in English.
- When updating architecture or team-process documentation, keep `docs/architecture/team-conventions.md` and `docs/architecture/architecture-rules.md` aligned if the change affects repository-wide conventions.
- Agent code quality rule: avoid duplicated literals (`path` fragments, magic strings, allowed-value sets). If repetition is local, extract a module-level constant; if repetition spans modules, use a shared constants/path module.
- QA/review agent rule: explicitly flag repeated literals and missing constant extraction as a quality finding (severity: at least `Minor`).
