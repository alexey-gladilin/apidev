---
name: /prompt-baseline-refresh
id: prompt-baseline-refresh
category: Productivity
description: Refresh prompt-guideline baseline for /prompt-improve and record what changed.
argument-hint: [optional note]
---

# Refresh Prompt Baseline

Goal: keep `/prompt-improve` aligned with the latest prompt-engineering guidance while preserving stable runtime behavior.

## Target File

- `.cursor/commands/prompt-improve.md`

## Sources

- Primary guide: `https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/`
- Raw source: `https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/gpt-5/codex_prompting_guide.ipynb`

## Process

1. Read current `.cursor/commands/prompt-improve.md`.
2. Check source guidance for material updates.
3. Update in `prompt-improve.md`:
   - `Last checked` date;
   - `Guide snapshot hash`;
   - rewrite rules/structure only if needed;
   - `Baseline Change Log` entry with concise summary.
4. Preserve command invariants:
   - no auto-execution;
   - no answering original task;
   - output language follows input language;
   - exact 4-section output format remains unchanged.
5. Run regression validation against `docs/prompt-improvement-regression-cases.md`.
6. Keep changes minimal and deterministic.

## Material Change Rule

- "Date-only" update is allowed only when source guidance has no material changes.
- In "no material changes" case, explicitly record:
  - checked date;
  - updated `Guide snapshot hash`;
  - rationale: `No material baseline changes detected`.
- If material changes are detected, update at least one of:
  - `Principles Matrix`;
  - `Rewrite Rules`;
  - `Safety` constraints;
  - `Output Format` constraints.

## Output (Required)

Return exactly:

1. `Baseline Status`
2. `Changes Applied`
3. `Material Change Verdict`
4. `No-Regression Check`

### Output Requirements

- `Baseline Status`: checked date + whether meaningful source changes were found.
- `Changes Applied`: bullet list of edits in `prompt-improve.md` (or `No changes`).
- `Material Change Verdict`: one of `Material updates applied` or `No material baseline changes`.
- `No-Regression Check`: confirm all invariants remain intact.

## Safety

If source guidance is unavailable, do not guess. Report `Baseline Status` as unavailable and do not modify behavioral invariants.
