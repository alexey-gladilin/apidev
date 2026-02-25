# Project Context

## Purpose
`apidev` is a contract-driven API development tool in the dev-tools family.
Its purpose is to reduce repetitive FastAPI scaffolding while keeping business logic manual and maintainable.
The tool takes declarative API contracts (YAML) and generates deterministic, safe-to-regenerate code for transport layers (routes/schemas/errors/OpenAPI metadata).
It is designed to work standalone and optionally integrate with `dbspec` for type/nullability/reference hints.

## Tech Stack
- Python 3.11+ for CLI/runtime tooling
- FastAPI as the target server framework in generated projects
- Pydantic for generated request/response/error schemas
- Jinja2 templates for code generation
- YAML contracts as the source format (`.apidev/contracts/**/*.yaml`)
- TOML config (`.apidev/config.toml`)
- OpenAPI as generated API documentation output
- Optional integration with `dbspec` as read-only source of DB metadata

## Project Conventions

### Code Style
- Keep generated and manual code strictly separated.
- Prefer deterministic output: same input contracts must produce identical generated files.
- Naming:
- Files: `snake_case`
- Python classes: `PascalCase`
- Python functions/variables: `snake_case`
- `operation_id` is derived from relative contract path:
- `<domain>/<file_stem>.yaml` -> `<domain>_<file_stem>`
- Example: `billing/create_invoice.yaml` -> `billing_create_invoice`

### Architecture Patterns
- Onion-style layering across dev-tools: `uidev -> apidev -> dbspec`.
- `apidev` has two runtimes:
- Tool runtime: validate contracts, compute diff, render templates, generate code.
- Target app runtime: generated transport + manual business handlers + bridge layer.
- In target projects, use three code zones:
- `generated/` for regenerated artifacts (routes, transport schemas, wrappers)
- `manual/` for business logic (handlers/services/repositories)
- `manual/runtime` for bridge concerns (handler registry, error mapping, auth hooks)
- Generated routes call stable handler interfaces by `operation_id`, not direct domain implementations.

### Testing Strategy
- Validate-first workflow:
- `apidev validate` before generation
- `apidev diff` to inspect planned changes
- `apidev generate` to apply
- Prefer contract tests for generated endpoints (smoke + key error paths).
- Add CI drift checks using generation check mode (`--check`) to ensure committed generated files match contracts.
- Protect manual code during regeneration with tests that assert generated-only overwrite behavior.

### Git Workflow
- Contracts are first-class project artifacts and should be committed.
- Recommended to commit:
- `.apidev/contracts/`
- `.apidev/templates/` (if customized)
- `.apidev/config.toml` when shared team config is desired
- Do not commit local temporary files or local-only artifacts.
- Keep commits scoped by concern (contracts, templates, generated output, manual logic).

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
- `dbspec` owns DB schema artifacts.
- Integration is optional and read-only from lower layer to upper layer.

## Important Constraints
- Regeneration safety is critical: overwrite only generated files; never overwrite manual files.
- Output must be deterministic and idempotent.
- `operation_id` must be stable and unique at project scope.
- Avoid generating business logic, repository internals, or policy engine internals.
- Keep auth and domain error policy manual in bridge layer while exposing declared behavior in generated OpenAPI metadata.
- Tooling should support incremental adoption in existing projects (module-by-module rollout).

## External Dependencies
- FastAPI runtime in target applications
- OpenAPI consumers (Swagger UI, client generators, docs pipelines)
- Optional `dbspec` project data for schema-derived hints (types, nullability, refs, enums)
- Git for versioning contracts/templates/generated artifacts
