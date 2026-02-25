# Architecture Validation Blueprint

## Purpose

This blueprint describes how architecture docs become executable guardrails in CI.

## Input Artifacts

- [Architecture Baseline](./README.md)
- [Architecture Rules](./architecture-rules.md)
- Source code under `src/apidev/*`

## Validation Phases

### Phase 1: Static Import Checks

- Parse Python AST for all modules under `src/apidev`.
- Build import graph between top-level packages: `apidev.commands`, `apidev.application`, `apidev.core`, `apidev.infrastructure`.
- Assert graph against `AR-001`.

### Phase 2: Forbidden Dependency Checks

- For `AR-002`, fail if `apidev.application.*` imports from `apidev.infrastructure.*`.
- For `AR-003`, fail if `apidev.core.*` imports file-format or I/O concerns directly.

### Phase 3: Behavioral Architecture Checks

- Validate `AR-005` with integration tests where `diff` produces plan only and `generate --check` detects drift without writes.
- Validate `AR-006` with negative tests for out-of-root paths.

## Suggested Test Layout

```text
tests/
  unit/
    architecture/
      test_layering_imports.py
      test_application_no_infra_imports.py
      test_core_purity.py
  contract/
    architecture/
      test_pipeline_contract.py
      test_write_boundary_policy.py
```

## Rule Traceability Matrix

| Rule ID | Primary Check | Suggested Test |
|---|---|---|
| AR-001 | Import graph allowed edges | `test_layering_imports.py` |
| AR-002 | No infra imports in app layer | `test_application_no_infra_imports.py` |
| AR-003 | No direct I/O/format handling in core | `test_core_purity.py` |
| AR-004 | Command thinness (optional metrics) | `test_command_thinness.py` |
| AR-005 | Pipeline and side-effect behavior | `test_pipeline_contract.py` |
| AR-006 | Out-of-bound write rejection | `test_write_boundary_policy.py` |
| AR-007 | Config path consistency checks | `test_config_path_single_source.py` |

## CI Integration (Target)

- Add architecture test subset to mandatory CI stage.
- Fail PR when any `AR-*` check fails.
- Keep error output in format: `RULE_ID | file:line | message`.

## Change Management

- Any architecture rule update must update `architecture-rules.md`, relevant tests, and OpenSpec architecture requirements (if behavior-level change).
