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
  - Legacy helpers (optional/internal): `/research-codebase`, `/design-feature`.
- Source of truth:
  - Core change files under `openspec/changes/<change-id>/`.
  - Artifact folders under `openspec/changes/<change-id>/artifacts/{research,design,plan}`.
  - `tasks.md` is the execution tracker; only orchestrator updates task statuses (single writer rule).

## Repository Conventions

- Project documentation must be written in Russian.
- Code comments, docstrings, identifiers, test names, CLI flags, and other code artifacts must be written in English.
- When updating architecture or team-process documentation, keep `docs/architecture/team-conventions.md` and `docs/architecture/architecture-rules.md` aligned if the change affects repository-wide conventions.
