---
name: /improve-prompt
id: improve-prompt
category: Productivity
description: Improve a raw prompt into a clear, execution-ready prompt with manual review and no auto-run.
argument-hint: [goal/task] [raw prompt or constraints]
---

# Improve Prompt (Manual Review, No Auto-Execution)

Goal: turn a rough user request into a high-quality prompt that is easy to review, edit, and copy into a new chat.

## Reference Baseline

- Primary guide: `https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/`
- Raw source: `https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/gpt-5/codex_prompting_guide.ipynb`
- Last checked: `2026-02-27`
- Guide snapshot hash: `c866c21fcdd1`

Use this baseline for prompt-quality principles (clarity, constraints, explicit output format, safe defaults).
Do not fetch web content on every command run.

## Principles Matrix

- `P1 Intent Fidelity`: preserve user goal and constraints without semantic drift.
- `P2 Clarity`: remove ambiguity, vague wording, and filler.
- `P3 Context Discipline`: include only context that improves execution quality.
- `P4 Explicit Deliverables`: require concrete output structure and success criteria.
- `P5 Safety by Default`: add safe defaults and confirmation gates for risky actions.
- `P6 Determinism First`: strict version must be repeatable and bounded.
- `P7 Language Consistency`: output language follows input language unless explicitly overridden.
- `P8 Non-Execution`: produce improved prompts only; never execute the underlying task.

## Core Behavior

- Do not execute the improved prompt.
- Do not start implementation from the improved prompt.
- Produce candidate prompt text only.
- Keep intent unchanged unless ambiguity blocks quality.
- Never answer the user's original question/task content. Rewrite only.
- Keep output language the same as the user's input language unless user explicitly asks for another language.

## Inputs

Use command arguments as the primary input. If missing, ask for:
- task/goal;
- raw prompt draft;
- context (project, stack, files, constraints);
- preferred style (`strict` or `creative`).

If arguments contain file refs (for example `@path:line-line`), treat them as context pointers only.
Do not infer "create/modify these files" unless the draft explicitly asks to implement changes.

## Rewrite Rules

1. Preserve user intent and constraints (`P1`).
2. Remove ambiguity and filler (`P2`).
3. Add explicit success criteria (`P4`).
4. Add relevant context sections only when useful (`P3`).
5. Prefer concrete, testable wording over generic language (`P2`, `P4`).
6. Keep output compact and practical (`P3`, `P6`).
7. If the user asks questions, convert them into a better prompt; do not provide answers (`P8`).
8. If required context is missing, add a short clarification block inside the improved prompt instead of guessing (`P2`, `P3`).
9. Align structure with the Reference Baseline unless it conflicts with explicit user constraints (`P1`).
10. Ensure strict version is deterministic and bounded; keep creative version exploratory but constrained (`P6`).

## Output Format (Required)

Return exactly these sections:

1. `Improved Prompt (Strict)`
2. `Improved Prompt (Creative)`
3. `What Changed`
4. `Review Checklist`

Do not add extra sections. Do not add analysis outside these sections.

### Section Requirements

- `Improved Prompt (Strict)`:
  - deterministic wording;
  - explicit constraints;
  - execution boundaries;
  - expected output format.

- `Improved Prompt (Creative)`:
  - same intent;
  - more exploratory style;
  - still bounded by constraints.

- `What Changed`:
  - 3-7 concise bullets;
  - focus on clarity, scope, constraints, and structure.

- `Review Checklist`:
  - intent preserved;
  - constraints correct;
  - sensitive actions excluded;
  - ready to paste into a new chat.

## Safety

If the draft asks for risky or destructive actions, keep the improved prompt but add explicit guardrails (confirmation step, non-destructive defaults, validation first).

## Sync Policy

- Re-check the Primary guide every `2-4 weeks` or before major workflow updates.
- When guidance changes, update this command and refresh `Last checked`.
- Keep updates deterministic: baseline is reviewed manually, not auto-pulled at runtime.
- If baseline changed materially, update at least one `Principles Matrix` item or `Rewrite Rules` mapping.
- Update `Guide snapshot hash` on every refresh to make "changed vs unchanged" auditable.
- Validate changes against `docs/prompt-improvement-regression-cases.md`.

## Baseline Change Log

- `2026-02-27`: Refresh baseline; source fetched (Codex prompting guide ipynb); snapshot hash set to `c866c21fcdd1`. No material baseline changes detected.
- `2026-02-27`: Added `Principles Matrix`, P-mapping in rewrite rules, snapshot-hash field, and mandatory regression checks.
- `2026-02-27`: Refresh baseline check; source unchanged (Codex prompting guide); last-checked date updated.
- `2026-02-26`: Baseline section introduced (source links, last-checked date, sync policy).
