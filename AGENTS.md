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
  - `/openspec-proposal` for change scaffolding (`proposal.md`, `design.md`, `tasks.md`, spec deltas, artifacts).
  - `/research-codebase` for fact-only research artifacts.
  - `/design-feature` for Design -> Plan artifacts bound to the same change.
  - `/openspec-implement` (multi-agent) or `/openspec-implement-single` (single-agent) for implementation.
- Source of truth:
  - Core change files under `openspec/changes/<change-id>/`.
  - Artifact folders under `openspec/changes/<change-id>/artifacts/{research,design,plan}`.
  - `tasks.md` is the execution tracker; only orchestrator updates task statuses (single writer rule).
