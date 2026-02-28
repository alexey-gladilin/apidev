# Project Context

## Purpose
`apidev` is a contract-driven API development tool in the dev-tools family.
Its purpose is to reduce repetitive FastAPI scaffolding while keeping business logic manual and maintainable.
The tool takes declarative API contracts (YAML) and generates deterministic, safe-to-regenerate code for transport layers (routes/schemas/errors/OpenAPI metadata).

## Tech Stack
- Python 3.11+ for CLI/runtime tooling
- FastAPI as the target server framework in generated projects
- Pydantic for generated request/response/error schemas
- Jinja2 templates for code generation
- YAML contracts as the source format (`.apidev/contracts/**/*.yaml`)
- TOML config (`.apidev/config.toml`)
- OpenAPI as generated API documentation output

## Project Conventions

### Code Style
- Keep generated and manual code strictly separated.
- Prefer deterministic output: same input contracts must produce identical generated files.
- Detailed naming and language policy lives in:
  - `docs/architecture/team-conventions.md`
  - `docs/architecture/patterns-and-naming.md`
  - `docs/reference/glossary.md`

### Architecture Patterns
- Detailed architecture baseline and rules live in:
  - `docs/architecture/architecture-overview.md`
  - `docs/architecture/architecture-rules.md`
  - `docs/architecture/validation-blueprint.md`

### Testing Strategy
- Validate-first workflow:
  - `apidev validate`
  - `apidev diff`
  - `apidev gen`
- Full testing policy lives in `docs/process/testing-strategy.md`.

### Git Workflow
- Contracts are first-class project artifacts and should be committed.
- Process guidance for contributors lives in `CONTRIBUTING.md`.

## Domain Context
`apidev` models API contracts per endpoint, not one giant spec file.
Domain boundaries are represented as folders under `.apidev/contracts/` (for example, `billing/`, `auth/`).
Each contract describes:
- HTTP method/path/auth
- request/query shape
- success response
- explicit error contracts (code, status, body)

Ownership model:
- `apidev` owns HTTP/API contract artifacts.

## Important Constraints
- Regeneration safety is critical: overwrite only generated files; never overwrite manual files.
- Output must be deterministic and idempotent.
- `operation_id` must be stable and unique at project scope.
- Avoid generating business logic, repository internals, or policy engine internals.
- Keep auth and domain error policy manual in bridge layer while exposing declared behavior in generated OpenAPI metadata.
- Tooling should support incremental adoption in existing projects (module-by-module rollout).
- Canonical generation command in repository documentation is `apidev gen`; `apidev generate` is a compatibility alias.

## External Dependencies
- FastAPI runtime in target applications
- OpenAPI consumers (Swagger UI, client generators, docs pipelines)
- Git for versioning contracts/templates/generated artifacts
