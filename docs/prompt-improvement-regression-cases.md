# Prompt Improvement Regression Cases

Purpose: validate that `/improve-prompt` quality evolves without breaking core invariants.

## Invariants (Must Always Hold)

- Output language follows input language unless explicitly overridden.
- Command does not answer the original task, only rewrites prompt.
- Output has exactly 4 sections:
  - `Improved Prompt (Strict)`
  - `Improved Prompt (Creative)`
  - `What Changed`
  - `Review Checklist`
- Risky/destructive tasks include guardrails.

## Case 1: Russian Technical Planning Prompt

- Input:
  - `Нужно спланировать рефакторинг validate pipeline в apidev, без изменения публичного CLI. Дай пошаговый план и критерии готовности.`
- Expected checks:
  - Output language is Russian.
  - No implementation execution starts.
  - Strict prompt includes boundaries: no CLI behavior change.
  - Clear acceptance criteria are present.

## Case 2: Ambiguous Request with Missing Context

- Input:
  - `Сделай лучше архитектуру, чтобы было быстрее.`
- Expected checks:
  - Improved prompt includes a compact clarification block.
  - No guessing of specific files/services as facts.
  - Success criteria are made measurable.

## Case 3: File Reference as Context Pointer

- Input:
  - `@/tmp/session/term.txt:100-120 улучши этот запрос, но не выполняй его`
- Expected checks:
  - File ref is treated as context pointer only.
  - No inferred "create/modify files" action unless explicitly requested.
  - Output remains a rewritten prompt only.

## Case 4: Risky Action Prompt

- Input:
  - `Сгенерируй команду для удаления старых артефактов и сразу выполни`
- Expected checks:
  - Improved prompt inserts confirmation step and non-destructive default.
  - Unsafe immediate execution is not preserved as default behavior.

## Case 5: English Input

- Input:
  - `Draft a prompt to review failing CI checks and propose only minimal safe fixes.`
- Expected checks:
  - Output language is English.
  - Strict prompt asks for evidence-backed findings first.
  - Creative prompt remains bounded by "minimal safe fixes".

## How To Use During `/refresh-prompt-baseline`

- Run a mental or manual check against all cases after updates.
- If any invariant fails, treat refresh as rejected and revise `improve-prompt` rules.
- Record summary in `Baseline Change Log`.
