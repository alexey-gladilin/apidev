# APIDev Architecture

## Purpose

This document captures the current high-level architecture of APIDev and target refactoring direction for maintainability and architecture validation.

Authoritative behavior requirements remain in `openspec/specs/`.

## Architecture Document Set

For full architecture documentation (including C4 Level 1/2/3 and validation rules), use:

- `docs/architecture/README.md`
- `docs/architecture/c4-context.md`
- `docs/architecture/c4-container.md`
- `docs/architecture/c4-components.md`
- `docs/architecture/architecture-rules.md`

## As-Is Layered View

```mermaid
flowchart TD
    CLI["CLI\nsrc/apidev/cli.py + src/apidev/commands/*"] --> APP["Application / Use-cases\nsrc/apidev/application/*"]
    APP --> CORE["Domain/Core\nsrc/apidev/core/*"]
    APP --> INFRA["Infrastructure Adapters\nsrc/apidev/infrastructure/*"]
    INFRA --> FS["Local File System\n.apidev/* + generated files"]
```

## Key Flow: Validate

```mermaid
sequenceDiagram
    participant U as User
    participant CMD as commands/validate_cmd
    participant SVC as application/ValidateService
    participant LD as infrastructure/YamlContractLoader
    participant RULE as core/rules/operation_id

    U->>CMD: apidev validate
    CMD->>SVC: run(project_dir)
    SVC->>LD: load(project_dir)
    LD-->>SVC: operations
    SVC->>RULE: ensure_unique_operation_ids(operations)
    SVC-->>CMD: ValidationResult
    CMD-->>U: diagnostics + exit code
```

## Key Flow: Diff

```mermaid
sequenceDiagram
    participant U as User
    participant CMD as commands/diff_cmd
    participant SVC as application/DiffService
    participant CFG as core/models/ApidevConfig
    participant LD as infrastructure/YamlContractLoader
    participant RND as infrastructure/JinjaTemplateRenderer
    participant FS as infrastructure/LocalFileSystem

    U->>CMD: apidev diff
    CMD->>SVC: run(project_dir)
    SVC->>CFG: load(project_dir)
    SVC->>LD: load(project_dir)
    SVC->>RND: render templates
    SVC->>FS: compare with existing files
    SVC-->>CMD: GenerationPlan(changes)
    CMD-->>U: file-level diff preview
```

## Key Flow: Generate

```mermaid
sequenceDiagram
    participant U as User
    participant CMD as commands/generate_cmd
    participant GENSVC as application/GenerateService
    participant DIFF as application/DiffService
    participant WR as infrastructure/SafeWriter

    U->>CMD: apidev generate [--check]
    CMD->>GENSVC: run(project_dir, check)
    GENSVC->>DIFF: run(project_dir)
    DIFF-->>GENSVC: plan(changes)

    alt check=true
        GENSVC-->>CMD: drift_detected=true|false
    else check=false
        GENSVC->>WR: write only ADD/UPDATE changes
        WR-->>GENSVC: writes inside generated root only
    end

    CMD-->>U: applied changes / drift status
```

## Target Refactoring Direction

```mermaid
flowchart TD
    CLI["CLI presentation"] --> ORCH["Thin orchestrators (commands)"]
    ORCH --> APP["Application services via ports"]
    APP --> CORE["Core models/rules/ports"]
    APP --> ADP["Infrastructure adapters"]

    CORE -. no dependency on .-> CLI
    CORE -. no dependency on .-> ADP
```

## Design Principles

- Single Responsibility: command parsing/presentation, orchestration, domain logic, and adapters stay separated.
- Dependency direction: core does not depend on application/commands/infrastructure.
- DRY: configuration paths and pipeline steps have a single source.
- Safety: writes are constrained to generated root.
- Determinism: same contracts/templates/config produce the same generation output.

## Related Documents

- `docs/architecture/README.md`
- `docs/architecture/architecture-rules.md`
- `docs/architecture/validation-blueprint.md`
- `openspec/changes/add-apidev-cli-tool-architecture/specs/cli-tool-architecture/spec.md`
- `docs/apidev-concept-and-approach.md`

